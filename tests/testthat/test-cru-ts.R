test_that("list_cru_ts_variables returns correct structure", {
  vars <- list_cru_ts_variables()
  expect_s3_class(vars, "data.frame")
  expect_true(all(c("variable", "name", "description", "unit", "era5_equivalent") %in% names(vars)))
  expect_equal(nrow(vars), 10L)
  expect_true("tmp" %in% vars$variable)
  expect_true("pre" %in% vars$variable)
  expect_true("tmx" %in% vars$variable)
  expect_true("tmn" %in% vars$variable)
})

test_that("list_cru_ts_variables has common names column", {
  vars <- list_cru_ts_variables()
  tmp_row <- vars[vars$variable == "tmp", ]
  expect_equal(tmp_row$name, "mean_temperature")
  expect_equal(tmp_row$era5_equivalent, "2m_temperature")
})

test_that(".cru_ts_url builds correct URL", {
  url <- varunayan:::.cru_ts_url("tmp", 1981L, 1990L)
  expect_match(url, "cru_ts4\\.07\\.1981\\.1990\\.tmp\\.dat\\.nc\\.gz")
  expect_match(url, "crudata\\.uea\\.ac\\.uk")
  expect_match(url, "/tmp/")
})

test_that(".cru_ts_needed_decades returns correct files", {
  decades <- varunayan:::.cru_ts_needed_decades(1981L, 2000L)
  expect_equal(length(decades), 2L)
  expect_equal(decades[[1]], c(1981L, 1990L))
  expect_equal(decades[[2]], c(1991L, 2000L))
})

test_that(".cru_ts_needed_decades handles partial overlap", {
  decades <- varunayan:::.cru_ts_needed_decades(1985L, 1995L)
  expect_equal(length(decades), 2L)
  expect_equal(decades[[1]][1], 1981L)
  expect_equal(decades[[2]][2], 2000L)
})

test_that(".cru_ts_needed_decades handles single decade", {
  decades <- varunayan:::.cru_ts_needed_decades(1985L, 1989L)
  expect_equal(length(decades), 1L)
  expect_equal(decades[[1]], c(1981L, 1990L))
})

test_that(".cru_ts_needed_decades handles final partial decade (2021-2022)", {
  decades <- varunayan:::.cru_ts_needed_decades(2020L, 2022L)
  expect_equal(length(decades), 2L)
  end_years <- sapply(decades, function(d) d[2])
  expect_true(2022L %in% end_years)
})

test_that(".validate_cru_ts_inputs rejects invalid variable", {
  expect_error(
    varunayan:::.validate_cru_ts_inputs("xyz", 1981L, 2010L),
    "not a valid CRU TS variable"
  )
})

test_that(".validate_cru_ts_inputs rejects out-of-range years", {
  expect_error(
    varunayan:::.validate_cru_ts_inputs("tmp", 1800L, 2010L),
    "1901-2022"
  )
  expect_error(
    varunayan:::.validate_cru_ts_inputs("tmp", 1981L, 2025L),
    "1901-2022"
  )
  expect_error(
    varunayan:::.validate_cru_ts_inputs("tmp", 2010L, 2005L),
    "start_year must be"
  )
})

test_that("cru_ts_bbox validates bounding box", {
  expect_error(
    cru_ts_bbox("tmp", 1981L, 2010L, north = -10, south = 10, east = 40, west = -10),
    "Invalid bounding box"
  )
})

test_that("cru_ts_geojson errors on missing file", {
  expect_error(
    cru_ts_geojson("tmp", 1981L, 2010L, geojson_file = "/nonexistent.geojson"),
    "not found"
  )
})

test_that(".parse_cru_ts_time handles days since", {
  dates <- varunayan:::.parse_cru_ts_time(c(0, 31, 59), "days since 1901-01-01")
  expect_s3_class(dates, "Date")
  expect_equal(format(dates[1], "%Y-%m-%d"), "1901-01-01")
  expect_equal(format(dates[2], "%Y-%m-%d"), "1901-02-01")
})

test_that("CRU TS aliases are functions", {
  expect_true(is.function(varunayan::CRUTSBbox))
  expect_true(is.function(varunayan::CRUTSGeojson))
  expect_true(is.function(varunayan::ListCRUTSVariables))
})

test_that("list_cru_ts_variables has hadex3_equivalent column", {
  vars <- list_cru_ts_variables()
  expect_true("hadex3_equivalent" %in% names(vars))
  # dtr should map to DTR
  dtr_row <- vars[vars$variable == "dtr", ]
  expect_equal(dtr_row$hadex3_equivalent, "DTR")
  # frs should map to FD
  frs_row <- vars[vars$variable == "frs", ]
  expect_equal(frs_row$hadex3_equivalent, "FD")
})

cru_fx_mock_get <- function(fixture_nc, status = 200L, env = parent.frame()) {
  seen <- new.env()
  seen$urls <- character(0)
  testthat::local_mocked_bindings(
    GET = function(url, ...) {
      seen$urls <- c(seen$urls, url)
      args <- list(...)
      disk <- Filter(function(a) inherits(a, "request") && !is.null(a$output$path), args)
      if (status == 200L && length(disk) > 0) {
        cru_fx_gzip(fixture_nc, disk[[1]]$output$path)
      }
      structure(list(status_code = status), class = "response")
    },
    status_code = function(x) x$status_code,
    .package = "httr",
    .env = env
  )
  seen
}

test_that(".read_cru_ts_nc reads values, coordinates and drops fill", {
  f <- tempfile(fileext = ".nc")
  cru_fx_write_nc(f, "tmp")
  df <- varunayan:::.read_cru_ts_nc(f, "tmp")
  expect_equal(names(df), c("year", "month", "latitude", "longitude", "value", "variable"))
  # 3 lon x 2 lat x 3 times, one filled cell removed
  expect_equal(nrow(df), 17L)
  expect_equal(unique(df$variable), "tmp")
  expect_false(any(df$year == 1981 & df$month == 1 & df$longitude == 72.25 & df$latitude == 18.25))
  v <- df$value[df$year == 1982 & df$longitude == 80.25 & df$latitude == 18.75]
  expect_equal(v, cru_fx_value(3, 2, 3), tolerance = 1e-5)
  expect_setequal(paste(df$year, df$month), c("1981 1", "1981 2", "1982 1"))
})

test_that(".read_cru_ts_nc errors on missing variable", {
  f <- tempfile(fileext = ".nc")
  cru_fx_write_nc(f, "tmp")
  expect_error(varunayan:::.read_cru_ts_nc(f, "pre"), "Variable 'pre' not found in NetCDF. Available: tmp, stn")
})

test_that(".parse_cru_ts_time handles months since and bad units", {
  d <- varunayan:::.parse_cru_ts_time(c(0, 1, 12, 13), "months since 1900-11-15")
  expect_equal(d, as.Date(c("1900-11-01", "1900-12-01", "1901-11-01", "1901-12-01")))
  expect_error(varunayan:::.parse_cru_ts_time(1, "hours since 1900-01-01"), "Unrecognised time units")
})

test_that(".decompress_gz round-trips", {
  src <- tempfile(fileext = ".nc")
  cru_fx_write_nc(src)
  gz <- tempfile(fileext = ".nc.gz")
  cru_fx_gzip(src, gz)
  out1 <- tempfile(fileext = ".nc")
  expect_equal(varunayan:::.decompress_gz(gz, out1), out1)
  expect_equal(unname(tools::md5sum(out1)), unname(tools::md5sum(src)))
})

test_that(".download_cru_ts_decade downloads, decompresses and reads", {
  imd_fx_local_cache()
  src <- tempfile(fileext = ".nc")
  cru_fx_write_nc(src, "pre")
  seen <- cru_fx_mock_get(src)
  out_dir <- tempfile("cru")
  dir.create(out_dir)
  df <- suppressMessages(varunayan:::.download_cru_ts_decade("pre", 1981L, 1990L, out_dir, use_cache = FALSE))
  expect_equal(nrow(df), 17L)
  expect_equal(unique(df$variable), "pre")
  expect_match(seen$urls, "cru_ts4\\.07\\.1981\\.1990\\.pre\\.dat\\.nc\\.gz$")
  # gz and nc temporaries removed
  expect_length(list.files(out_dir), 0L)
})

test_that(".download_cru_ts_decade saves to (mocked) cache when enabled", {
  cache <- imd_fx_local_cache()
  src <- tempfile(fileext = ".nc")
  cru_fx_write_nc(src, "tmp")
  cru_fx_mock_get(src)
  out_dir <- tempfile("cru")
  dir.create(out_dir)
  df <- suppressMessages(varunayan:::.download_cru_ts_decade("tmp", 1981L, 1990L, out_dir, use_cache = TRUE))
  cached <- list.files(cache, full.names = TRUE)
  expect_length(cached, 1L)
  expect_equal(readRDS(cached), df)
})

test_that(".download_cru_ts_decade errors on HTTP failure and GET error", {
  imd_fx_local_cache()
  cru_fx_mock_get(tempfile(), status = 404L)
  out_dir <- tempfile("cru")
  dir.create(out_dir)
  expect_error(
    suppressMessages(varunayan:::.download_cru_ts_decade("tmp", 1981L, 1990L, out_dir, FALSE)),
    "HTTP 404 for CRU TS tmp 1981-1990"
  )
  local_mocked_bindings(GET = function(...) stop("no route"), .package = "httr")
  expect_error(
    suppressMessages(varunayan:::.download_cru_ts_decade("tmp", 1981L, 1990L, out_dir, FALSE)),
    "Download failed: no route"
  )
})

test_that(".fetch_cru_ts combines decades and trims to year range", {
  calls <- list()
  local_mocked_bindings(
    .download_cru_ts_decade = function(variable, decade_start, decade_end, output_dir, use_cache) {
      calls[[length(calls) + 1]] <<- c(decade_start, decade_end)
      data.frame(
        year = c(decade_start, decade_end), month = 1L, latitude = 20,
        longitude = 75, value = c(1, 2), variable = variable
      )
    }
  )
  out <- varunayan:::.fetch_cru_ts("tmp", 1990L, 2001L, use_cache = FALSE, output_dir = tempdir())
  expect_equal(calls, list(c(1981L, 1990L), c(1991L, 2000L), c(2001L, 2010L)))
  expect_equal(out$year, c(1990L, 1991L, 2000L, 2001L))
  expect_equal(rownames(out), as.character(1:4))
})

test_that("cru_ts_bbox end-to-end filters space and time", {
  imd_fx_local_cache()
  src <- tempfile(fileext = ".nc")
  cru_fx_write_nc(src, "tmp")
  cru_fx_mock_get(src)
  out <- suppressMessages(cru_ts_bbox(
    "tmp", 1981L, 1981L,
    north = 19, south = 18, east = 73, west = 72,
    output_dir = tempfile("cru"), use_cache = FALSE
  ))
  # lons 72.25/72.75 x lats 18.25/18.75 x 2 months, minus one fill
  expect_equal(nrow(out), 7L)
  expect_true(all(out$year == 1981L))
  expect_true(all(out$longitude < 73))
  v <- out$value[out$month == 2 & out$longitude == 72.75 & out$latitude == 18.75]
  expect_equal(v, cru_fx_value(2, 2, 2), tolerance = 1e-5)
})

test_that("cru_ts_geojson end-to-end uses polygon", {
  imd_fx_local_cache()
  src <- tempfile(fileext = ".nc")
  cru_fx_write_nc(src, "tmp")
  cru_fx_mock_get(src)
  gj <- tempfile(fileext = ".geojson")
  imd_fx_write_geojson(gj, 72.5, 18, 73, 19)
  out <- suppressMessages(cru_ts_geojson(
    "tmp", 1981L, 1982L, gj,
    output_dir = tempfile("cru"), use_cache = FALSE
  ))
  expect_equal(nrow(out), 6L)
  expect_true(all(out$longitude == 72.75))
  expect_setequal(out$year, c(1981L, 1982L))

  # region with no data points
  gj2 <- tempfile(fileext = ".geojson")
  imd_fx_write_geojson(gj2, 0, 0, 1, 1)
  out2 <- suppressMessages(cru_ts_geojson(
    "tmp", 1981L, 1981L, gj2,
    output_dir = tempfile("cru"), use_cache = FALSE
  ))
  expect_equal(nrow(out2), 0L)
})

test_that("CRU TS decades are served from cache on the second call", {
  imd_fx_local_cache()
  src <- tempfile(fileext = ".nc")
  cru_fx_write_nc(src, "pre")
  seen <- cru_fx_mock_get(src)
  out_dir <- tempfile("cru")
  dir.create(out_dir)
  first <- suppressMessages(varunayan:::.download_cru_ts_decade("pre", 1981L, 1990L, out_dir, use_cache = TRUE))
  expect_length(seen$urls, 1)
  expect_equal(suppressMessages(list_cache(source = "cru_ts"))$source, "cru_ts")
  second <- suppressMessages(varunayan:::.download_cru_ts_decade("pre", 1981L, 1990L, out_dir, use_cache = TRUE))
  expect_length(seen$urls, 1)
  expect_equal(second, first)
  expect_equal(suppressMessages(clear_cache(source = "cru_ts", confirm = FALSE)), 1)
})
