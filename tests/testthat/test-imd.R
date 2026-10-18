# Offline tests for IMD readers, processing, download layer and end-to-end flows.

test_that("get_imd_grid_specs returns expected specs", {
  rf <- get_imd_grid_specs("rainfall_0.25")
  expect_equal(rf$nlat, 129)
  expect_equal(rf$nlon, 135)
  expect_equal(rf$missing_value, -999)
  expect_equal(rf$variable_name, "RAINFALL")

  tmax <- get_imd_grid_specs("tmax_1.0")
  expect_equal(tmax$nlat, 31)
  expect_equal(tmax$nlon, 31)
  expect_equal(tmax$missing_value, 99.9)
  expect_equal(tmax$format, "Binary")
  expect_equal(length(seq(tmax$lat_start, tmax$lat_end, by = tmax$resolution)), tmax$nlat)

  expect_equal(get_imd_grid_specs("tmin_1.0")$unit, "Celsius")
  rf1 <- get_imd_grid_specs("rainfall_1.0")
  expect_equal(c(rf1$nlon, rf1$nlat), c(35, 33))
  expect_equal(length(seq(rf1$lon_start, rf1$lon_end, by = rf1$resolution)), rf1$nlon)
  expect_equal(length(seq(rf1$lat_start, rf1$lat_end, by = rf1$resolution)), rf1$nlat)
  expect_equal(length(seq(rf$lon_start, rf$lon_end, by = rf$resolution)), rf$nlon)
  expect_equal(length(seq(rf$lat_start, rf$lat_end, by = rf$resolution)), rf$nlat)
  expect_error(get_imd_grid_specs("foo"), "Invalid dataset. The dataset must be one of: rainfall_0.25")
})

test_that("list_imd_datasets returns the four datasets", {
  ds <- list_imd_datasets()
  expect_s3_class(ds, "data.frame")
  expect_equal(nrow(ds), 4L)
  expect_equal(ds$dataset_id, c("rainfall_0.25", "rainfall_1.0", "tmax_1.0", "tmin_1.0"))
  expect_equal(ds$missing_value, c(-999, -999, 99.9, 99.9))
  expect_equal(ds$format[ds$dataset_id == "tmax_1.0"], "Binary")
  expect_true(all(c("variable", "resolution", "year_start", "year_end", "unit", "grid_size") %in% names(ds)))
})

test_that("is_leap_year and extract_years_from_filenames", {
  expect_equal(varunayan:::is_leap_year(c(1900, 2000, 2023, 2024)), c(FALSE, TRUE, FALSE, TRUE))
  yrs <- varunayan:::extract_years_from_filenames(c("imd_tmax_1.0_2021.grd", "/x/imd_rainfall_0.25_2023.nc"))
  expect_equal(unname(yrs), c(2021L, 2023L))
  expect_error(varunayan:::extract_years_from_filenames("no_year.grd"), "Cannot extract the years")
})

test_that("read_imd_temperature round-trips known cell values and drops 99.9", {
  f <- tempfile(fileext = ".grd")
  imd_fx_write_temperature(f, 2023)
  df <- imd_fx_expect_msg(read_imd_temperature(f, "tmax", 2023), "Processed 730 data points")

  expect_equal(names(df), c("date", "latitude", "longitude", "temperature"))
  # Only the two non-missing cells survive, 365 days each
  expect_equal(nrow(df), 2L * 365L)
  expect_setequal(unique(df$longitude), c(72.5, 73.5))
  expect_equal(unique(df$latitude), 19.5)
  expect_s3_class(df$date, "Date")
  expect_equal(range(df$date), as.Date(c("2023-01-01", "2023-12-31")))

  day10 <- df[df$date == as.Date("2023-01-10"), ]
  expect_equal(day10$temperature[day10$longitude == 72.5], 21.0, tolerance = 1e-5)
  expect_equal(day10$temperature[day10$longitude == 73.5], 31.0, tolerance = 1e-5)
  expect_false(any(df$temperature >= 99))
})

test_that("read_imd_temperature handles leap years (366 days)", {
  f <- tempfile(fileext = ".grd")
  imd_fx_write_temperature(f, 2024,
    cells = data.frame(lon = 97.5, lat = 37.5, base = -5)
  )
  df <- suppressMessages(read_imd_temperature(f, "tmin", 2024))
  expect_equal(nrow(df), 366L)
  expect_true(as.Date("2024-02-29") %in% df$date)
  expect_equal(df$temperature[df$date == as.Date("2024-12-31")], -5 + 36.6, tolerance = 1e-5)
  expect_equal(unique(df$longitude), 97.5)
  expect_equal(unique(df$latitude), 37.5)
})

test_that("read_imd_temperature warns on truncated file and errors on missing file", {
  f <- tempfile(fileext = ".grd")
  imd_fx_write_temperature(f, 2023, n_days = 10L)
  expect_warning(
    suppressMessages(read_imd_temperature(f, "tmax", 2023)),
    "Expected 350765 values, but found 9610"
  )
  expect_error(read_imd_temperature(tempfile(), "tmax", 2023), "Cannot find the file")
  expect_error(suppressMessages(read_imd_temperature(f, "tavg", 2023)), "Invalid dataset")
})

test_that("read_imd_rainfall accepts 1.0 degree resolution as numeric", {
  f <- tempfile(fileext = ".nc")
  imd_fx_write_rainfall(f, 2023, lons = c(72.5, 73.5), lats = c(19.5, 20.5))
  df <- suppressMessages(read_imd_rainfall(f, 1.0, 2023))
  expect_equal(names(df), c("date", "latitude", "longitude", "rainfall"))
  expect_gt(nrow(df), 0)
})

test_that("read_imd_rainfall reads NetCDF via stars and drops -999", {
  f <- tempfile(fileext = ".nc")
  imd_fx_write_rainfall(f, 2023)
  df <- suppressMessages(read_imd_rainfall(f, 0.25, 2023))

  expect_equal(names(df), c("date", "latitude", "longitude", "rainfall"))
  expect_s3_class(df$date, "Date")
  # 3 x 2 grid, one cell entirely missing, 365 days
  expect_equal(nrow(df), 5L * 365L)
  expect_false(any(df$longitude == 72.25 & df$latitude == 19.0))
  expect_true(all(df$rainfall > -900))

  v <- df$rainfall[df$date == as.Date("2023-03-01") & df$longitude == 72.75 & df$latitude == 19.25]
  expect_equal(v, imd_fx_rain_value(3, 2, 60))
  expect_equal(range(df$date), as.Date(c("2023-01-01", "2023-12-31")))
})

test_that("read_imd_rainfall falls back to ncdf4 when read_ncdf fails", {
  f <- tempfile(fileext = ".nc")
  imd_fx_write_rainfall(f, 2023)
  local_mocked_bindings(read_ncdf = function(...) stop("boom"))
  expect_warning(
    df <- suppressMessages(read_imd_rainfall(f, 0.25, 2023)),
    "read_ncdf failed. The function will try ncdf4: boom"
  )
  expect_equal(nrow(df), 5L * 365L)
  expect_true(all(c("date", "latitude", "longitude", "rainfall") %in% names(df)))
  v <- df$rainfall[df$date == as.Date("2023-01-05") &
    as.numeric(df$longitude) == 72.5 & as.numeric(df$latitude) == 19.0]
  expect_equal(v, imd_fx_rain_value(2, 1, 5))
})

test_that("read_imd_rainfall errors on missing file or bad resolution", {
  expect_error(read_imd_rainfall(tempfile(), 0.25, 2023), "Cannot find the file")
  f <- tempfile(fileext = ".nc")
  imd_fx_write_rainfall(f, 2023)
  expect_error(suppressMessages(read_imd_rainfall(f, 0.5, 2023)), "Invalid dataset")
})

test_that("process_imd_files combines multiple temperature years in order", {
  d <- tempfile("imdproc")
  dir.create(d)
  f1 <- file.path(d, "imd_tmax_1.0_2022.grd")
  f2 <- file.path(d, "imd_tmax_1.0_2023.grd")
  imd_fx_write_temperature(f1, 2022, cells = data.frame(lon = 80.5, lat = 25.5, base = 10))
  imd_fx_write_temperature(f2, 2023, cells = data.frame(lon = 80.5, lat = 25.5, base = 40))

  # years inferred from filenames
  out <- suppressMessages(process_imd_files(c(f2, f1), "tmax"))
  expect_equal(nrow(out), 730L)
  expect_false(is.unsorted(out$date))
  expect_equal(out$date[1], as.Date("2022-01-01"))
  expect_equal(out$temperature[1], 10.1, tolerance = 1e-5)
  expect_equal(out$temperature[nrow(out)], 40 + 36.5, tolerance = 1e-5)
  expect_equal(rownames(out)[1:3], c("1", "2", "3"))
})

test_that("process_imd_files reads rainfall and infers resolution from filename", {
  f <- file.path(tempfile("imdrain"), "imd_rainfall_0.25_2023.nc")
  dir.create(dirname(f))
  imd_fx_write_rainfall(f, 2023)
  out <- suppressMessages(process_imd_files(f, "rain"))
  expect_equal(nrow(out), 5L * 365L)
  expect_equal(names(out), c("date", "latitude", "longitude", "rainfall"))
})

test_that("process_imd_files validates inputs", {
  expect_error(process_imd_files(character(0), "tmax"), "The file list is empty")
  expect_error(
    process_imd_files(c("a_2020.grd", "b_2021.grd"), "tmax", years = 2020),
    "The number of years must be equal to the number of files"
  )
  f <- tempfile(fileext = "_2023.grd")
  imd_fx_write_temperature(f, 2023)
  expect_error(
    suppressMessages(process_imd_files(f, "humidity", years = 2023)),
    "Invalid var_type: humidity"
  )
  expect_error(
    suppressMessages(process_imd_files("missing_2023.grd", "tmax")),
    "Cannot process missing_2023.grd: Cannot find the file"
  )
})

imd_fx_small_df <- function() {
  data.frame(
    date = rep(as.Date("2023-01-01") + 0:1, each = 4),
    latitude = rep(c(18.5, 18.5, 21.5, 25.5), 2),
    longitude = rep(c(73.5, 79.5, 74.5, 74.5), 2),
    rainfall = 1:8
  )
}

test_that("filter_imd_by_bbox keeps exactly the cells inside the box", {
  df <- imd_fx_small_df()
  out <- imd_fx_expect_msg(
    filter_imd_by_bbox(df, north = 22, south = 18, east = 76, west = 72),
    "Filtered 8 points to 4 in the bounding box"
  )
  expect_equal(nrow(out), 4L)
  expect_setequal(paste(out$latitude, out$longitude), c("18.5 73.5", "21.5 74.5"))
  expect_equal(out$rainfall, c(1L, 3L, 5L, 7L))

  # inclusive boundaries
  edge <- suppressMessages(filter_imd_by_bbox(df, north = 21.5, south = 18.5, east = 74.5, west = 73.5))
  expect_equal(nrow(edge), 4L)
})

test_that("filter_imd_by_bbox validates inputs", {
  expect_error(filter_imd_by_bbox(data.frame(x = 1), 22, 18, 76, 72), "must contain 'latitude' and 'longitude'")
  expect_error(filter_imd_by_bbox(imd_fx_small_df(), 18, 22, 76, 72), "Invalid bounding box")
})

test_that("filter_imd_by_geojson keeps points inside polygon", {
  gj <- tempfile(fileext = ".geojson")
  imd_fx_write_geojson(gj, 72, 18, 76, 22)
  df <- imd_fx_small_df()
  out <- suppressMessages(filter_imd_by_geojson(df, gj))
  expect_equal(nrow(out), 4L)
  expect_equal(out$rainfall, c(1L, 3L, 5L, 7L))
  expect_error(filter_imd_by_geojson(data.frame(a = 1), gj), "must contain 'latitude' and 'longitude'")
})

test_that("filter_imd_by_geojson treats edges as straight lon/lat lines and keeps them", {
  gj <- tempfile(fileext = ".geojson")
  imd_fx_write_geojson(gj, 72, 18, 78, 22)
  grid <- expand.grid(longitude = seq(71, 79, by = 0.25), latitude = seq(17, 23, by = 0.25))
  df <- data.frame(date = as.Date("2019-07-01"), grid, rainfall = 1)
  old_s2 <- sf::sf_use_s2()
  out <- suppressMessages(filter_imd_by_geojson(df, gj))
  expect_identical(sf::sf_use_s2(), old_s2)
  box <- suppressMessages(filter_imd_by_bbox(df, north = 22, south = 18, east = 78, west = 72))
  expect_equal(out, box)
  expect_equal(sum(out$latitude == 18), sum(out$latitude == 22)) # both parallels kept
})

test_that("aggregate_imd_by_frequency sums rainfall monthly", {
  df <- data.frame(
    date = rep(seq(as.Date("2023-01-30"), as.Date("2023-02-02"), by = "day"), each = 2),
    latitude = 20,
    longitude = rep(c(73, 74), 4),
    rainfall = c(1, 10, 2, 20, 3, 30, NA, 40)
  )
  out <- suppressMessages(aggregate_imd_by_frequency(df, "monthly"))
  expect_equal(nrow(out), 4L)
  expect_true(all(c("date", "latitude", "longitude", "rainfall") %in% names(out)))
  jan73 <- out$rainfall[out$date == as.Date("2023-01-01") & out$longitude == 73]
  feb73 <- out$rainfall[out$date == as.Date("2023-02-01") & out$longitude == 73]
  feb74 <- out$rainfall[out$date == as.Date("2023-02-01") & out$longitude == 74]
  expect_equal(jan73, 1 + 2)
  expect_equal(feb73, 3) # NA dropped
  expect_equal(feb74, 30 + 40)
  expect_false(is.unsorted(out$date))
})

test_that("aggregate_imd_by_frequency averages temperature and handles yearly", {
  df <- data.frame(
    date = as.Date(c("2022-06-01", "2022-07-01", "2023-01-01", "2023-01-02")),
    latitude = 20, longitude = 73,
    temperature = c(30, 40, 10, 20)
  )
  yr <- suppressMessages(aggregate_imd_by_frequency(df, "Yearly"))
  expect_equal(yr$date, as.Date(c("2022-01-01", "2023-01-01")))
  expect_equal(yr$temperature, c(35, 15))

  mo <- suppressMessages(aggregate_imd_by_frequency(df, "monthly"))
  expect_equal(mo$temperature, c(30, 40, 15))

  # unknown frequency falls back to monthly grouping
  other <- suppressMessages(aggregate_imd_by_frequency(df, "weekly"))
  expect_equal(other$temperature, mo$temperature)
  expect_equal(other$date, mo$date)

  expect_identical(aggregate_imd_by_frequency(df, "DAILY"), df)
})

test_that("aggregate_imd_by_frequency validates inputs", {
  expect_error(aggregate_imd_by_frequency(data.frame(x = 1), "monthly"), "must contain a 'date'")
  expect_error(
    aggregate_imd_by_frequency(data.frame(date = Sys.Date(), latitude = 1, longitude = 1), "monthly"),
    "Cannot find a value column"
  )
})

test_that("save_imd_results writes csv, coordinates and metadata", {
  out_dir <- tempfile("imdout")
  df <- imd_fx_small_df()
  res <- suppressMessages(varunayan:::save_imd_results(df, "req1", "rainfall", 0.25, "daily", out_dir))
  sub <- file.path(out_dir, "req1_imd_output")
  expect_equal(res, file.path(sub, "req1_imd_rainfall_0.25_daily_data.csv"))
  expect_true(file.exists(res))

  back <- utils::read.csv(res)
  expect_equal(nrow(back), 8L)
  expect_equal(names(back), names(df))

  coords <- utils::read.csv(file.path(sub, "req1_unique_coordinates.csv"))
  expect_equal(nrow(coords), 4L)

  meta <- jsonlite::fromJSON(file.path(sub, "req1_metadata.json"))
  expect_equal(meta$request_id, "req1")
  expect_equal(meta$n_records, 8L)
  expect_equal(meta$n_locations, 4L)
  expect_equal(meta$date_range, c("2023-01-01", "2023-01-02"))
  expect_equal(meta$spatial_extent, c(18.5, 25.5, 73.5, 79.5))
})

imd_fx_mock_httr <- function(resp, env = parent.frame()) {
  local_mocked_bindings(
    POST = function(...) if (inherits(resp, "error")) stop(resp) else resp,
    status_code = function(x) x$status,
    headers = function(x) list(`content-type` = x$content_type),
    content = function(x, ...) x$body,
    .env = env
  )
}

test_that("download_imd_year writes response body on success", {
  out <- tempfile(fileext = ".grd")
  imd_fx_mock_httr(imd_fx_response(body = as.raw(1:16)))
  res <- varunayan:::download_imd_year(2023, "maxtemp.php", "maxtemp", "https://example.invalid/", out, max_retries = 1)
  expect_equal(res, out)
  expect_equal(readBin(out, "raw", n = 100), as.raw(1:16))
})

test_that("download_imd_year retries server errors and reports the last one", {
  local_mocked_bindings(Sys.sleep = function(...) NULL, .package = "base")
  imd_fx_mock_httr(imd_fx_response(status = 503L))
  warns <- character()
  expect_error(
    withCallingHandlers(
      varunayan:::download_imd_year(2023, "a.php", "a", "https://example.invalid/", tempfile(), max_retries = 2),
      warning = function(w) {
        warns <<- c(warns, conditionMessage(w))
        invokeRestart("muffleWarning")
      }
    ),
    "Failed after 2 attempts. Last error: Server returned status 503"
  )
  expect_equal(warns, sprintf("Attempt %d/2 failed: Server returned status 503", 1:2))
})

test_that("download_imd_year fails at once on a response without data", {
  calls <- 0
  count <- function(resp) {
    local_mocked_bindings(
      POST = function(...) {
        calls <<- calls + 1
        resp
      },
      status_code = function(x) x$status,
      headers = function(x) list(`content-type` = x$content_type),
      content = function(x, ...) x$body,
      .env = parent.frame()
    )
  }
  get <- function() varunayan:::download_imd_year(1950, "a.php", "a", "https://example.invalid/", tempfile())
  count(imd_fx_response(content_type = "text/html; charset=UTF-8"))
  expect_error(get(), "HTML instead of data for 1950")
  count(imd_fx_response(body = raw(0)))
  expect_error(get(), "empty")
  count(imd_fx_response(status = 404L))
  expect_error(get(), "status 404")
  expect_equal(calls, 3)
})

test_that("download_imd_year errors when connection fails", {
  imd_fx_mock_httr(simpleError("could not resolve host"))
  expect_warning(
    expect_error(
      varunayan:::download_imd_year(2023, "a.php", "a", "https://example.invalid/", tempfile(), max_retries = 1),
      "Last error: could not resolve host"
    ),
    "Attempt 1/1 failed"
  )
})

test_that("check_imd_server reflects status code, errors and retries", {
  calls <- 0
  local_mocked_bindings(Sys.sleep = function(...) NULL, .package = "base")
  local_mocked_bindings(
    HEAD = function(...) {
      calls <<- calls + 1
      if (calls < 3) stop("tls handshake") else list(status = 200L)
    },
    status_code = function(x) x$status
  )
  expect_true(varunayan:::check_imd_server("https://example.invalid/", timeout = 1))
  expect_equal(calls, 3)

  local_mocked_bindings(HEAD = function(...) list(status = 404L))
  expect_true(varunayan:::check_imd_server("https://example.invalid/", timeout = 1))

  local_mocked_bindings(HEAD = function(...) list(status = 502L))
  expect_false(varunayan:::check_imd_server("https://example.invalid/", timeout = 1, retries = 2))

  calls <- 0
  local_mocked_bindings(HEAD = function(...) {
    calls <<- calls + 1
    stop("timeout")
  })
  expect_false(varunayan:::check_imd_server("https://example.invalid/", timeout = 1, retries = 2))
  expect_equal(calls, 2)
})

test_that("download_imd_rainfall validates arguments", {
  expect_error(download_imd_rainfall(1900, 1901), "1901-2025")
  expect_error(download_imd_rainfall(2020, 2026), "1901-2025")
  expect_error(download_imd_rainfall(2021, 2020), "Start year must be <= end year")
  expect_error(download_imd_rainfall(2020, 2020, resolution = 0.5), "Resolution must be 0.25 or 1.0")
})

test_that("download_imd_temperature validates arguments", {
  expect_error(download_imd_temperature(1950, 1960), "1951-2025")
  expect_error(download_imd_temperature(2021, 2020), "Start year must be <= end year")
  expect_error(download_imd_temperature(2020, 2020, var_type = "tavg"), "var_type must be 'tmax' or 'tmin'")
})

test_that("download_imd_rainfall downloads, caches, then reuses cache", {
  cache <- imd_fx_local_cache()
  src <- tempfile(fileext = ".nc")
  imd_fx_write_rainfall(src, 2023)
  out_dir <- tempfile("imddl")
  calls <- character(0)
  local_mocked_bindings(
    check_imd_server = function(...) TRUE,
    download_imd_year = function(year, php_file, param_name, base_url, output_file, max_retries = 3) {
      calls <<- c(calls, paste(year, php_file, param_name))
      file.copy(src, output_file, overwrite = TRUE)
      output_file
    }
  )
  files <- imd_fx_expect_msg(
    download_imd_rainfall(2023, 2023, resolution = 0.25, output_dir = out_dir),
    "Download is necessary for 1 year"
  )
  expect_equal(calls, "2023 RF25.php RF25")
  expect_equal(files, file.path(out_dir, "imd_rainfall_0.25_2023.nc"))
  expect_true(file.exists(files))
  expect_equal(length(list.files(cache, pattern = "^imd_20230101_20231231_.*\\.nc$")), 1L)

  # Second call: served from cache, no download
  unlink(files)
  files2 <- imd_fx_expect_msg(
    download_imd_rainfall(2023, 2023, resolution = 0.25, output_dir = out_dir),
    "All the requested data is in the cache"
  )
  expect_equal(length(calls), 1L)
  expect_true(file.exists(files2))
  expect_equal(unname(tools::md5sum(files2)), unname(tools::md5sum(src)))
})

test_that("download_imd_rainfall uses 1.0 endpoint and no cache", {
  imd_fx_local_cache()
  calls <- character(0)
  local_mocked_bindings(
    check_imd_server = function(...) TRUE,
    download_imd_year = function(year, php_file, param_name, base_url, output_file, ...) {
      calls <<- c(calls, paste(base_url, php_file, param_name))
      writeBin(as.raw(1:4), output_file)
      output_file
    }
  )
  files <- suppressMessages(download_imd_rainfall(2001, 2002, resolution = 1.0, output_dir = tempfile("dl"), use_cache = FALSE))
  expect_equal(calls, rep("https://imdpune.gov.in/cmpg/Griddata/ rainfallone.php rainone", 2))
  expect_equal(basename(files), c("imd_rainfall_1_2001.nc", "imd_rainfall_1_2002.nc"))
})

test_that("download_imd_rainfall stops when server is down and data not cached", {
  imd_fx_local_cache()
  local_mocked_bindings(check_imd_server = function(...) FALSE)
  expect_warning(
    expect_error(
      suppressMessages(download_imd_rainfall(2023, 2023, output_dir = tempfile("dl"))),
      "Cannot connect to the server, and 1 year\\(s\\) are not in the cache"
    ),
    "does not respond"
  )
})

test_that("download_imd_rainfall surfaces per-year download failure", {
  imd_fx_local_cache()
  local_mocked_bindings(
    check_imd_server = function(...) TRUE,
    download_imd_year = function(...) stop("server exploded")
  )
  expect_error(
    suppressMessages(download_imd_rainfall(2023, 2023, output_dir = tempfile("dl"))),
    "Download failed for 2023: server exploded"
  )
})

test_that("download_imd_temperature downloads, caches and reuses cache", {
  cache <- imd_fx_local_cache()
  src <- tempfile(fileext = ".grd")
  imd_fx_write_temperature(src, 2023)
  calls <- character(0)
  local_mocked_bindings(
    check_imd_server = function(...) TRUE,
    download_imd_year = function(year, php_file, param_name, base_url, output_file, ...) {
      calls <<- c(calls, php_file)
      file.copy(src, output_file, overwrite = TRUE)
      output_file
    }
  )
  out_dir <- tempfile("imddl")
  files <- suppressMessages(download_imd_temperature(2023, 2023, var_type = "tmin", output_dir = out_dir))
  expect_equal(calls, "mintemp.php")
  expect_equal(basename(files), "imd_tmin_1.0_2023.grd")
  expect_equal(length(list.files(cache, pattern = "\\.grd$")), 1L)

  files2 <- imd_fx_expect_msg(
    download_imd_temperature(2023, 2023, var_type = "tmin", output_dir = out_dir),
    "Use of cached data for 2023"
  )
  expect_equal(length(calls), 1L)
  expect_true(file.exists(files2))

  # tmax endpoint, cache disabled
  files3 <- suppressMessages(download_imd_temperature(2023, 2023, var_type = "tmax", output_dir = out_dir, use_cache = FALSE))
  expect_equal(calls[2], "maxtemp.php")
  expect_equal(basename(files3), "imd_tmax_1.0_2023.grd")
})

test_that("download_imd_temperature errors when server down or download fails", {
  imd_fx_local_cache()
  local_mocked_bindings(check_imd_server = function(...) FALSE)
  expect_warning(
    expect_error(
      suppressMessages(download_imd_temperature(2023, 2024, output_dir = tempfile("dl"))),
      "Cannot connect to the server, and 2 year\\(s\\) are not in the cache"
    ),
    "does not respond"
  )
  local_mocked_bindings(
    check_imd_server = function(...) TRUE,
    download_imd_year = function(...) stop("bad gateway")
  )
  expect_error(
    suppressMessages(download_imd_temperature(2023, 2023, output_dir = tempfile("dl"), use_cache = FALSE)),
    "Download failed for 2023: bad gateway"
  )
})

imd_fx_mock_rain_download <- function(env = parent.frame()) {
  local_mocked_bindings(
    download_imd_rainfall = function(start_year, end_year, resolution, output_dir, use_cache) {
      dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
      vapply(start_year:end_year, function(y) {
        f <- file.path(output_dir, sprintf("imd_rainfall_%s_%d.nc", resolution, y))
        imd_fx_write_rainfall(f, y)
        f
      }, character(1))
    },
    .env = env
  )
}


test_that("imd_rainfall_bbox monthly end-to-end", {
  imd_fx_mock_rain_download()
  out_dir <- tempfile("e2e")
  res <- suppressMessages(imd_rainfall_bbox(
    "rq", 2023, 2023,
    north = 19.1, south = 18.9, east = 73, west = 72,
    resolution = 0.25, frequency = "monthly", output_dir = out_dir
  ))
  # lat 19.0 row: lon 72.25 missing, keeps 72.5 and 72.75 -> 2 cells x 12 months
  expect_equal(nrow(res), 24L)
  expect_setequal(unique(res$longitude), c(72.5, 72.75))
  jan <- res$rainfall[res$date == as.Date("2023-01-01") & res$longitude == 72.5]
  expect_equal(jan, sum(imd_fx_rain_value(2, 1, 1:31)))

  sub <- file.path(out_dir, "rq_imd_output")
  expect_true(file.exists(file.path(sub, "rq_imd_rainfall_0.25_monthly_data.csv")))
  expect_true(file.exists(file.path(sub, "rq_metadata.json")))
  # raw file cleaned up because save_raw = FALSE
  expect_false(file.exists(file.path(out_dir, "imd_rainfall_0.25_2023.nc")))
})

test_that("imd_rainfall_bbox daily keeps raw files when save_raw = TRUE", {
  imd_fx_mock_rain_download()
  out_dir <- tempfile("e2e")
  res <- suppressMessages(imd_rainfall_bbox(
    "rq2", 2023, 2023,
    north = 20, south = 19.1, east = 73, west = 72,
    save_raw = TRUE, output_dir = out_dir
  ))
  expect_equal(nrow(res), 3L * 365L)
  expect_true(all(res$latitude == 19.25))
  expect_true(file.exists(file.path(out_dir, "imd_rainfall_0.25_2023.nc")))
  expect_error(
    suppressMessages(imd_rainfall_bbox("x", 2023, 2023, north = 18, south = 19, east = 73, west = 72)),
    "Invalid bounding box"
  )
})

test_that("imd_rainfall_bbox errors when nothing downloaded", {
  local_mocked_bindings(download_imd_rainfall = function(...) character(0))
  expect_error(
    suppressMessages(imd_rainfall_bbox("x", 2023, 2023, 20, 19, 73, 72, output_dir = tempfile())),
    "All file downloads failed"
  )
})

test_that("imd_rainfall_geojson yearly end-to-end", {
  imd_fx_mock_rain_download()
  gj <- tempfile(fileext = ".geojson")
  imd_fx_write_geojson(gj, 72.4, 18.9, 72.6, 19.3)
  out_dir <- tempfile("e2e")
  res <- suppressMessages(imd_rainfall_geojson(
    "gq", 2023, 2023, gj,
    frequency = "yearly", output_dir = out_dir
  ))
  expect_equal(nrow(res), 2L)
  expect_equal(unique(res$longitude), 72.5)
  expect_equal(res$date, as.Date(c("2023-01-01", "2023-01-01")))
  expect_equal(res$rainfall[res$latitude == 19.0], sum(imd_fx_rain_value(2, 1, 1:365)))
  expect_true(file.exists(file.path(out_dir, "gq_imd_output", "gq_imd_rainfall_0.25_yearly_data.csv")))

  expect_error(
    suppressMessages(imd_rainfall_geojson("gq", 2023, 2023, tempfile(fileext = ".geojson"))),
    "Cannot find the GeoJSON file"
  )
  local_mocked_bindings(download_imd_rainfall = function(...) character(0))
  expect_error(
    suppressMessages(imd_rainfall_geojson("gq", 2023, 2023, gj, output_dir = out_dir)),
    "All file downloads failed"
  )
})

test_that("imd_temperature_bbox monthly uses mean", {
  imd_fx_mock_temp_download()
  out_dir <- tempfile("e2e")
  res <- suppressMessages(imd_temperature_bbox(
    "tq", 2023, 2023,
    north = 20, south = 19, east = 73, west = 72,
    var_type = "tmax", frequency = "monthly", output_dir = out_dir
  ))
  expect_equal(nrow(res), 12L)
  expect_equal(unique(res$longitude), 72.5)
  expect_equal(res$temperature[1], 20 + mean(1:31) / 10, tolerance = 1e-5)
  expect_equal(res$temperature[2], 20 + mean(32:59) / 10, tolerance = 1e-5)
  expect_true(file.exists(file.path(out_dir, "tq_imd_output", "tq_imd_tmax_1_monthly_data.csv")))
  expect_false(file.exists(file.path(out_dir, "imd_tmax_1.0_2023.grd")))

  expect_error(
    suppressMessages(imd_temperature_bbox("tq", 2023, 2023, 19, 20, 73, 72)),
    "Invalid bounding box"
  )
  local_mocked_bindings(download_imd_temperature = function(...) character(0))
  expect_error(
    suppressMessages(imd_temperature_bbox("tq", 2023, 2023, 20, 19, 73, 72, output_dir = out_dir)),
    "All file downloads failed"
  )
})

test_that("imd_temperature_geojson daily end-to-end", {
  imd_fx_mock_temp_download()
  gj <- tempfile(fileext = ".geojson")
  imd_fx_write_geojson(gj, 73, 19, 74, 20)
  out_dir <- tempfile("e2e")
  res <- suppressMessages(imd_temperature_geojson(
    "tg", 2023, 2023, gj,
    var_type = "tmin", output_dir = out_dir, save_raw = TRUE
  ))
  expect_equal(nrow(res), 365L)
  expect_equal(unique(res$longitude), 73.5)
  expect_equal(res$temperature[res$date == as.Date("2023-12-31")], 30 + 36.5, tolerance = 1e-5)
  expect_true(file.exists(file.path(out_dir, "imd_tmin_1.0_2023.grd")))
  expect_true(file.exists(file.path(out_dir, "tg_imd_output", "tg_imd_tmin_1_daily_data.csv")))

  expect_error(
    suppressMessages(imd_temperature_geojson("tg", 2023, 2023, tempfile(fileext = ".geojson"))),
    "Cannot find the GeoJSON file"
  )
  local_mocked_bindings(download_imd_temperature = function(...) character(0))
  expect_error(
    suppressMessages(imd_temperature_geojson("tg", 2023, 2023, gj, output_dir = out_dir)),
    "All file downloads failed"
  )
})
