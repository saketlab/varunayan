# Tests for R/core.R. All CDS access is mocked; nothing touches the network.

test_that("estimate_cds_fields counts variables x timesteps x levels", {
  expect_equal(estimate_cds_fields(2, "2023-01-01", "2023-01-10", "hourly"), 2L * 10L * 24L)
  expect_equal(estimate_cds_fields(3, "2023-01-01", "2023-01-10", "daily"), 30L)
  expect_equal(estimate_cds_fields(1, "2023-01-01", "2023-01-01", "daily", 5), 5L)
  # Nov 2022 .. Feb 2024 = 16 months
  expect_equal(estimate_cds_fields(2, "2022-11-15", "2024-02-01", "monthly"), 32L)
  expect_equal(estimate_cds_fields(1, "2023-03-01", "2023-03-31", "monthly", 3L), 3L)
  expect_type(estimate_cds_fields(1, "2023-01-01", "2023-01-02", "hourly"), "integer")
})

test_that("compute_optimal_chunk_size respects CDS limits", {
  # hourly: 120000 %/% (1 * 24) = 5000 days, capped at 3650
  expect_equal(compute_optimal_chunk_size(1, "hourly"), 3650L)
  expect_equal(compute_optimal_chunk_size(5, "hourly"), 1000L)
  expect_equal(compute_optimal_chunk_size(2, "hourly", n_pressure_levels = 10), 250L)
  expect_equal(compute_optimal_chunk_size(1, "daily"), 3650L)
  expect_equal(compute_optimal_chunk_size(100, "daily"), 1200L)
  # never below one day
  expect_equal(compute_optimal_chunk_size(10000, "hourly"), 1L)
  # monthly: 9000 %/% (n * 12) years, capped to [1, 30]
  expect_equal(compute_optimal_chunk_size(1, "monthly"), 30L)
  expect_equal(compute_optimal_chunk_size(50, "monthly"), 15L)
  expect_equal(compute_optimal_chunk_size(1000, "monthly"), 1L)

  # chunk size times fields per day never exceeds the limit
  for (n in c(1, 3, 7, 25)) {
    days <- compute_optimal_chunk_size(n, "hourly")
    expect_lte(n * 24 * days, CDS_FIELD_LIMIT_HOURLY)
  }
})

test_that("convert_era5_units converts K to C and m to mm only where needed", {
  df <- data.frame(
    variable = c("t2m", "2m_temperature", "tp", "total_precipitation", "sp", "mx2t"),
    value = c(273.15, 300, 0.001, 0.0025, 101325, 310.15),
    stringsAsFactors = FALSE
  )
  out <- convert_era5_units(df)
  expect_equal(out$value, c(0, 26.85, 1, 2.5, 101325, 37))

  # untouched when columns are absent
  x <- data.frame(a = 1)
  expect_identical(convert_era5_units(x), x)
})

test_that("convert_era5_units strips units class", {
  skip_if_not_installed("units")
  df <- data.frame(variable = "t2m", stringsAsFactors = FALSE)
  df$value <- units::set_units(300, "K")
  out <- convert_era5_units(df)
  expect_false(inherits(out$value, "units"))
  expect_equal(out$value, 300 - 273.15)
})

test_that("validate_era5_inputs normalises and rejects bad inputs", {
  v <- validate_era5_inputs("SINGLE", "2m_temperature", "2023-01-01", "2023-01-05")
  expect_equal(v$dataset_type, "single")
  expect_equal(v$start_dt, as.Date("2023-01-01"))
  expect_equal(v$end_dt, as.Date("2023-01-05"))

  expect_error(validate_era5_inputs("surface", "x", "2023-01-01", "2023-01-02"), "Invalid dataset_type: surface")
  expect_error(
    validate_era5_inputs("single", c("2m_temperature", "bogus"), "2023-01-01", "2023-01-02"),
    "Incorrect variables for single dataset: bogus"
  )
  expect_error(
    validate_era5_inputs("single", "2m_temperature", "2023-02-01", "2023-01-01"),
    "The start date must be before the end date"
  )
})

test_that("era5ify_bbox validates coordinates before downloading", {
  local_mocked_bindings(download_era5_data = function(...) stop("must not download"))
  call_bbox <- function(n, s, e, w) {
    era5ify_bbox("r", "2m_temperature", "2023-01-01", "2023-01-02",
      north = n, south = s, east = e, west = w, use_cache = FALSE
    )
  }
  expect_error(call_bbox(10, 20, 80, 70), "The north boundary must be more")
  expect_error(call_bbox(20, 10, 70, 80), "The east boundary must be more")
  expect_error(call_bbox(95, 10, 80, 70), "Incorrect coordinates")
  expect_error(call_bbox(20, 10, 190, 70), "Incorrect coordinates")
})

test_that("era5ify_point validates coordinates", {
  expect_error(era5ify_point("r", "2m_temperature", "2023-01-01", "2023-01-02", lat = 91, lon = 0), "Latitude")
  expect_error(era5ify_point("r", "2m_temperature", "2023-01-01", "2023-01-02", lat = 0, lon = -181), "Longitude")
})

test_that("era5ify_geojson errors for a missing GeoJSON file", {
  expect_error(
    era5ify_geojson("r", "2m_temperature", "2023-01-01", "2023-01-02",
      json_file = file.path(tempdir(), "missing.geojson")
    ),
    "Cannot find the GeoJSON file"
  )
})

# fixture time step is the chunk start date, exposing each requested range
era5_fake_downloader <- function(log, too_large_if = function(s, e) FALSE, ...) {
  log$calls <- list()
  extra <- list(...)
  function(variables, start_date, end_date, area = NULL, resolution = 0.25,
           frequency = "hourly", output_file, ...) {
    log$calls[[length(log$calls) + 1L]] <- list(
      start = as.Date(start_date), end = as.Date(end_date),
      area = area, output_file = output_file
    )
    if (too_large_if(as.Date(start_date), as.Date(end_date))) {
      stop(structure(
        class = c("cds_request_too_large", "error", "condition"),
        list(message = "CDS request too large", call = NULL)
      ))
    }
    do.call(era5_make_nc, c(list(
      path = output_file,
      times = as.POSIXct(as.character(as.Date(start_date)), tz = "UTC")
    ), extra))
    output_file
  }
}

test_that("download_era5_data returns a single file when one chunk suffices", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(download_era5_single = era5_fake_downloader(log))

  res <- suppressMessages(download_era5_data(
    "single", "2m_temperature", as.Date("2023-01-01"), as.Date("2023-01-10"),
    c(20, 77, 19.75, 77.5), 0.25, "hourly", d, "req"
  ))
  expect_named(res, "file")
  expect_true(file.exists(res$file))
  expect_length(log$calls, 1)
  expect_match(basename(log$calls[[1]]$output_file), "^req_chunk1_\\d{8}\\.nc$")
})

test_that("download_era5_data auto-chunks and combines multiple files", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(
    download_era5_single = era5_fake_downloader(log),
    compute_optimal_chunk_size = function(...) 4L
  )

  res <- NULL
  capture.output(res <- suppressMessages(download_era5_data(
    "single", "2m_temperature", as.Date("2023-01-01"), as.Date("2023-01-10"),
    NULL, 0.25, "daily", d, "req",
    verbose = TRUE
  )))
  expect_length(log$calls, 3)
  starts <- do.call(c, lapply(log$calls, `[[`, "start"))
  expect_equal(starts, as.Date(c("2023-01-01", "2023-01-05", "2023-01-09")))
  expect_named(res, c("data", "files"))
  expect_equal(nrow(res$data), 3 * 6)
  expect_equal(sort(unique(as.Date(res$data$datetime))), starts)
  # raw files removed unless save_raw = TRUE
  expect_false(any(file.exists(res$files)))
})

test_that("download_era5_data keeps raw chunk files with save_raw", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(
    download_era5_single = era5_fake_downloader(log),
    compute_optimal_chunk_size = function(...) 5L
  )
  capture.output(res <- suppressMessages(download_era5_data(
    "single", "2m_temperature", as.Date("2023-01-01"), as.Date("2023-01-10"),
    NULL, 0.25, "daily", d, "req",
    save_raw = TRUE
  )))
  expect_length(res$files, 2)
  expect_true(all(file.exists(res$files)))
})

test_that("download_era5_data splits chunks that CDS reports as too large", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(download_era5_single = era5_fake_downloader(
    log,
    too_large_if = function(s, e) as.numeric(e - s) >= 30
  ))

  res <- suppressMessages(download_era5_data(
    "single", "2m_temperature", as.Date("2023-01-01"), as.Date("2023-03-01"),
    NULL, 0.25, "hourly", d, "req"
  ))
  ok <- Filter(function(x) as.numeric(x$end - x$start) < 30, log$calls)
  ranges <- vapply(ok, function(x) paste(x$start, x$end), character(1))
  expect_equal(ranges, c(
    "2023-01-01 2023-01-29", "2023-01-30 2023-02-13", "2023-02-14 2023-03-01"
  ))
  expect_match(basename(ok[[3]]$output_file), "^req_chunk1bb_")
  expect_equal(nrow(res$data), 3 * 6)
})

test_that("download_era5_data gives up when splitting cannot help", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(download_era5_single = era5_fake_downloader(
    log,
    too_large_if = function(s, e) TRUE
  ))
  expect_error(
    suppressMessages(download_era5_data(
      "single", "2m_temperature", as.Date("2023-01-01"), as.Date("2023-01-20"),
      NULL, 0.25, "hourly", d, "req"
    )),
    "The request is still too large after the split to 19 days"
  )
})

test_that("download_era5_data uses year-aligned chunks for monthly data", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(download_era5_single = era5_fake_downloader(log))

  res <- suppressMessages(download_era5_data(
    "single", "2m_temperature", as.Date("2020-03-01"), as.Date("2021-05-31"),
    NULL, 0.25, "monthly", d, "req"
  ))
  expect_length(log$calls, 1)
  expect_equal(log$calls[[1]]$start, as.Date("2020-01-01"))
  expect_equal(log$calls[[1]]$end, as.Date("2021-12-31"))

  # Force multi-year chunking
  local_mocked_bindings(compute_optimal_chunk_size = function(...) 2L)
  capture.output(res <- suppressMessages(download_era5_data(
    "single", "2m_temperature", as.Date("2015-01-01"), as.Date("2019-12-31"),
    NULL, 0.25, "monthly", d, "req2"
  )))
  starts <- vapply(log$calls[-1], function(x) format(x$start), character(1))
  ends <- vapply(log$calls[-1], function(x) format(x$end), character(1))
  expect_equal(starts, c("2015-01-01", "2017-01-01", "2019-01-01"))
  expect_equal(ends, c("2016-12-31", "2018-12-31", "2019-12-31"))
})

test_that("download_era5_data splits too-large monthly requests at year boundaries", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(download_era5_single = era5_fake_downloader(
    log,
    too_large_if = function(s, e) as.numeric(e - s) > 400
  ))
  capture.output(res <- suppressMessages(download_era5_data(
    "single", "2m_temperature", as.Date("2018-01-01"), as.Date("2021-12-31"),
    NULL, 0.25, "monthly", d, "req"
  )))
  ok <- Filter(function(x) as.numeric(x$end - x$start) <= 400, log$calls)
  starts <- vapply(ok, function(x) format(x$start), character(1))
  expect_true(all(grepl("-01-01$", starts)))
  expect_equal(length(ok), 4)
})

test_that("download_era5_data routes pressure requests", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(
    download_era5_pressure = era5_fake_downloader(log),
    download_era5_single = function(...) stop("wrong downloader")
  )
  res <- suppressMessages(download_era5_data(
    "pressure", "temperature", as.Date("2023-01-01"), as.Date("2023-01-02"),
    NULL, 0.25, "hourly", d, "req",
    pressure_levels = c("500", "850")
  ))
  expect_true(file.exists(res$file))
  expect_length(log$calls, 1)
})

era5_mock_cds <- function(log = new.env(), ...) {
  local_mocked_bindings(
    get_cds_credentials = function(...) TRUE,
    wf_request = era5_fake_wf_request(log, ...),
    .env = parent.frame()
  )
  log
}

era5_two_vars <- list(
  t2m = era5_default_value,
  tp = function(lon, lat, tidx) tidx / 1000
)

test_that("era5ify_bbox (hourly) returns converted, bbox-filtered data", {
  era5_local_cache()
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- era5_mock_cds(vars = era5_two_vars)

  out <- suppressMessages(era5ify_bbox(
    "bbox_req", c("2m_temperature", "total_precipitation"),
    "2023-01-01", "2023-01-01",
    north = 20, south = 19.9, east = 77.6, west = 77,
    output_dir = d, use_cache = FALSE
  ))
  expect_equal(nrow(out), 3 * 1 * 2 * 2)
  expect_true(all(out$latitude == 20))
  t1 <- out[out$variable == "t2m" & out$longitude == 77 &
    format(out$datetime, "%H", tz = "UTC") == "00", "value"]
  expect_equal(t1, 280 + 20 + 7.7 + 1 - 273.15)
  expect_equal(sort(unique(out$value[out$variable == "tp"])), c(1, 2))
  # raw download removed by default
  expect_length(list.files(d, pattern = "\\.nc$"), 0)

  req <- log$requests[[1]]
  expect_equal(req$area, c(20, 77, 19.9, 77.6))
  expect_equal(unlist(req$variable), c("2m_temperature", "total_precipitation"))
})

test_that("era5ify_bbox keeps raw units and raw files when asked", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  era5_mock_cds()
  out <- suppressMessages(era5ify_bbox(
    "raw_req", "2m_temperature", "2023-01-01", "2023-01-01",
    north = 21, south = 19, east = 78, west = 76,
    output_dir = d, use_cache = FALSE, convert_units = FALSE, save_raw = TRUE,
    verbose = TRUE
  ))
  expect_equal(max(out$value), 280 + 20 + 7.75 + 2)
  expect_length(list.files(d, pattern = "\\.nc$"), 1)
})

test_that("era5ify_bbox (daily) aggregates to daily means in Celsius", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  era5_mock_cds()
  out <- suppressMessages(era5ify_bbox(
    "daily_req", "2m_temperature", "2023-01-01", "2023-01-01",
    north = 21, south = 19, east = 78, west = 76,
    frequency = "daily", output_dir = d, use_cache = FALSE
  ))
  expect_equal(nrow(out), 6)
  v <- out$value[out$latitude == 19.75 & out$longitude == 77.25]
  expect_equal(v, mean(280 + 19.75 + 7.725 + c(1, 2)) - 273.15)
})

test_that("era5ify_bbox (monthly) uses monthly means and adds year/month", {
  era5_local_cache()
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  times <- as.POSIXct(c("2023-01-01", "2023-02-01"), tz = "UTC")
  log <- era5_mock_cds(times = times)
  out <- suppressMessages(era5ify_bbox(
    "monthly_req", "2m_temperature", "2023-01-01", "2023-02-28",
    north = 21, south = 19, east = 78, west = 76,
    frequency = "monthly", output_dir = d, use_cache = TRUE
  ))
  expect_true(all(c("year", "month") %in% names(out)))
  expect_setequal(unique(out$month), c(1L, 2L))
  expect_equal(unique(out$year), 2023L)
  expect_equal(log$requests[[1]]$dataset_short_name, "reanalysis-era5-single-levels-monthly-means")
  # result was cached in the temp cache
  expect_equal(nrow(suppressMessages(list_cache("era5"))), 1)
})

test_that("era5ify_bbox combines multi-chunk downloads", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(
    download_era5_single = era5_fake_downloader(log),
    compute_optimal_chunk_size = function(...) 1L
  )
  capture.output(out <- suppressMessages(era5ify_bbox(
    "chunked", "2m_temperature", "2023-01-01", "2023-01-03",
    north = 21, south = 19, east = 78, west = 76,
    frequency = "daily", output_dir = d, use_cache = FALSE
  )))
  expect_length(log$calls, 3)
  expect_equal(nrow(out), 3 * 6)
  expect_equal(sort(unique(as.Date(out$datetime))), as.Date("2023-01-01") + 0:2)
})

test_that("era5ify_geojson filters to the polygon", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  gj <- era5_make_geojson(77.1, 77.6, 19.9, 20.1)
  on.exit(unlink(gj), add = TRUE)
  log <- era5_mock_cds()

  out <- suppressMessages(era5ify_geojson(
    "gj_req", "2m_temperature", "2023-01-01", "2023-01-01",
    json_file = gj, output_dir = d, use_cache = FALSE, verbose = TRUE
  ))
  expect_equal(nrow(out), 4)
  expect_setequal(unique(out$longitude), c(77.25, 77.5))
  expect_equal(log$requests[[1]]$area, c(20.1, 77.1, 19.9, 77.6))
  expect_length(list.files(d, pattern = "\\.nc$"), 0)

  daily <- suppressMessages(era5ify_geojson(
    "gj_req", "2m_temperature", "2023-01-01", "2023-01-01",
    json_file = gj, frequency = "daily", output_dir = d, use_cache = FALSE,
    convert_units = FALSE
  ))
  expect_equal(nrow(daily), 2)
  expect_equal(daily$value[daily$longitude == 77.5], 280 + 20 + 7.75 + 1.5)
})

test_that("era5ify_geojson filters combined multi-chunk data", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  gj <- era5_make_geojson(76.9, 77.1, 19.5, 20.5)
  on.exit(unlink(gj), add = TRUE)
  log <- new.env()
  local_mocked_bindings(
    download_era5_single = era5_fake_downloader(log),
    compute_optimal_chunk_size = function(...) 1L
  )
  capture.output(out <- suppressMessages(era5ify_geojson(
    "gj_chunks", "2m_temperature", "2023-01-01", "2023-01-02",
    json_file = gj, frequency = "daily", output_dir = d, use_cache = FALSE
  )))
  expect_length(log$calls, 2)
  expect_equal(nrow(out), 2 * 2) # lon 77 x 2 lats x 2 days
  expect_true(all(out$longitude == 77))
})

test_that("era5ify_point (pressure) returns the nearest cell", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- era5_mock_cds(vars = list(t = era5_default_value), plevel = 500)

  out <- suppressMessages(era5ify_point(
    "pt", "temperature", "2023-01-01", "2023-01-01",
    lat = 19.8, lon = 77.3, dataset_type = "pressure", pressure_levels = "500",
    output_dir = d, use_cache = FALSE
  ))
  expect_equal(nrow(out), 2)
  expect_true(all(out$latitude == 19.75 & out$longitude == 77.25))
  expect_equal(sort(out$value), 280 + 19.75 + 7.725 + c(1, 2) - 273.15)
  req <- log$requests[[1]]
  expect_equal(req$area, c(20.3, 76.8, 19.3, 77.8))
  expect_length(list.files(d, pattern = "\\.nc$"), 0)
})

test_that("era5ify_point (pressure) handles multi-chunk ranges", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(download_era5_pressure = era5_fake_downloader(log))

  out <- suppressMessages(era5ify_point(
    "pt", "temperature", "2010-01-01", "2020-02-15",
    lat = 20, lon = 77.5, dataset_type = "pressure", pressure_levels = "850",
    frequency = "daily", output_dir = d, use_cache = FALSE, convert_units = FALSE
  ))
  expect_length(log$calls, 2)
  expect_equal(log$calls[[2]]$start, as.Date("2010-01-01") + 3650)
  expect_equal(nrow(out), 2)
  expect_true(all(out$latitude == 20 & out$longitude == 77.5))
  expect_equal(out$value, rep(280 + 20 + 7.75 + 1, 2))
  expect_equal(as.Date(out$datetime), as.Date("2010-01-01") + c(0, 3650))
})

test_that("download_era5_data reports auto-chunking when over the field limit", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(download_era5_single = era5_fake_downloader(log))

  capture.output(msgs <- testthat::capture_messages(download_era5_data(
    "single", "2m_temperature", as.Date("2010-01-01"), as.Date("2023-12-31"),
    NULL, 0.25, "hourly", d, "big",
    verbose = TRUE
  )))
  expect_true(any(grepl("The package divides it into 3650-day chunks", msgs)))
  expect_length(log$calls, 2)
  expect_equal(log$calls[[2]]$start, as.Date("2010-01-01") + 3650)

  vars12 <- paste0("v", 1:12)
  capture.output(msgs <- testthat::capture_messages(download_era5_data(
    "single", vars12, as.Date("1940-01-01"), as.Date("2023-12-31"),
    NULL, 0.25, "monthly", d, "bigm",
    verbose = TRUE
  )))
  expect_true(any(grepl("The package divides it into 3 chunk\\(s\\) of a maximum of 30 year", msgs)))
})

test_that("era5ify_point works for single-level data (default dataset_type)", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- era5_mock_cds(vars = list(t2m = era5_default_value))

  out <- suppressMessages(era5ify_point(
    "pt", "2m_temperature", "2023-01-01", "2023-01-01",
    lat = 19.8, lon = 77.3, output_dir = d, use_cache = FALSE,
    use_timeseries_api = FALSE # the default would call the live timeseries API
  ))
  expect_gt(nrow(out), 0)
  expect_true(all(out$latitude == 19.75 & out$longitude == 77.25))
  expect_length(log$requests, 1)
})

test_that("era5ify_point single-level handles multi-chunk ranges", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(download_era5_single = era5_fake_downloader(log))

  out <- suppressMessages(era5ify_point(
    "pt", "2m_temperature", "2010-01-01", "2020-02-15",
    lat = 20, lon = 77.5, frequency = "daily", output_dir = d,
    use_cache = FALSE, convert_units = FALSE
  ))
  expect_length(log$calls, 2)
  expect_true(all(out$latitude == 20 & out$longitude == 77.5))
})
