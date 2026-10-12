test_that("list_hadex3_indices returns correct structure", {
  all_idx <- list_hadex3_indices()
  expect_s3_class(all_idx, "data.frame")
  expect_true(all(c("index", "category", "description", "unit", "annual", "monthly") %in% names(all_idx)))
  expect_true("TXx" %in% all_idx$index)
  expect_true("Rx1day" %in% all_idx$index)
})

test_that("list_hadex3_indices frequency filter works", {
  monthly <- list_hadex3_indices(frequency = "monthly")
  annual <- list_hadex3_indices(frequency = "annual")
  all_idx <- list_hadex3_indices(frequency = "all")

  expect_true(nrow(monthly) < nrow(all_idx))
  expect_true(nrow(annual) <= nrow(all_idx))
  expect_true(all(monthly$monthly))

  # Indices not available monthly should not appear
  expect_false("CSDI" %in% monthly$index)
  expect_false("GSL" %in% monthly$index)
  # But should appear in annual
  expect_true("CSDI" %in% annual$index)
})

test_that(".hadex3_url builds correct annual URL", {
  url <- varunayan:::.hadex3_url("TXx", "annual", "61-90")
  expect_match(url, "HadEX3_TXx_1901-2018_ADW_61-90_1.25x1.875deg.nc.gz")
  expect_match(url, "hadobs/hadex3/data")
})

test_that(".hadex3_url builds correct monthly URL", {
  url <- varunayan:::.hadex3_url("Rx1day", "monthly")
  expect_match(url, "HadEX3_Rx1day_MON.nc.gz")
})

test_that(".hadex3_url uses correct baseline", {
  url_6190 <- varunayan:::.hadex3_url("TX90p", "annual", "61-90")
  url_8110 <- varunayan:::.hadex3_url("TX90p", "annual", "81-10")
  expect_match(url_6190, "61-90")
  expect_match(url_8110, "81-10")
})

test_that(".validate_hadex3_inputs rejects invalid index", {
  expect_error(
    varunayan:::.validate_hadex3_inputs("INVALID", "annual", "61-90", 1981, 2010),
    "not available"
  )
})

test_that(".validate_hadex3_inputs rejects out-of-range years", {
  expect_error(
    varunayan:::.validate_hadex3_inputs("TXx", "annual", "61-90", 1800, 2010),
    "1901-2018"
  )
  expect_error(
    varunayan:::.validate_hadex3_inputs("TXx", "annual", "61-90", 1981, 2025),
    "1901-2018"
  )
})

test_that(".validate_hadex3_inputs rejects monthly-only index for monthly", {
  # CSDI is annual-only
  expect_error(
    varunayan:::.validate_hadex3_inputs("CSDI", "monthly", "61-90", 1981, 2010),
    "not available"
  )
})

test_that(".validate_hadex3_inputs rejects 81-10 baseline for unsupported index", {
  expect_error(
    varunayan:::.validate_hadex3_inputs("TXx", "annual", "81-10", 1981, 2010),
    "81-10"
  )
})

test_that(".parse_hadex3_years handles 'years since' units", {
  years <- varunayan:::.parse_hadex3_years(0:5, "years since 1901-01-01")
  expect_equal(years, 1901:1906)
})

test_that(".parse_hadex3_years handles 'days since' units", {
  # 0 days since 1901-01-01 = 1901, 365 days = 1902
  years <- varunayan:::.parse_hadex3_years(c(0, 365), "days since 1901-01-01")
  expect_equal(years[1], 1901L)
  expect_equal(years[2], 1902L)
})

test_that(".parse_hadex3_months handles 'months since' units", {
  ym <- varunayan:::.parse_hadex3_months(0:2, "months since 1901-01-15")
  expect_equal(ym$year, c(1901L, 1901L, 1901L))
  expect_equal(ym$month, c(1L, 2L, 3L))
})

test_that("hadex3_bbox validates bounding box", {
  expect_error(
    hadex3_bbox("TXx", 1981, 2010, north = -10, south = 10, east = 40, west = -10),
    "Invalid bounding box"
  )
})

test_that("hadex3_geojson errors on missing GeoJSON", {
  expect_error(
    hadex3_geojson("TXx", 1981, 2010, geojson_file = "/nonexistent/file.geojson"),
    "not found"
  )
})

test_that("HadEX3 aliases exist and are exported", {
  expect_true(existsMethod("HadEX3Bbox") || is.function(varunayan::HadEX3Bbox))
  expect_true(is.function(varunayan::HadEX3Geojson))
  expect_true(is.function(varunayan::ListHadEX3Indices))
})

hadex_fx_mock_get <- function(fixture_nc, status = 200L, empty = FALSE, env = parent.frame()) {
  seen <- new.env()
  seen$urls <- character(0)
  testthat::local_mocked_bindings(
    GET = function(url, ...) {
      seen$urls <- c(seen$urls, url)
      disk <- Filter(function(a) inherits(a, "request") && !is.null(a$output$path), list(...))
      if (status == 200L && length(disk) > 0) {
        if (empty) file.create(disk[[1]]$output$path) else cru_fx_gzip(fixture_nc, disk[[1]]$output$path)
      }
      structure(list(status_code = status), class = "response")
    },
    status_code = function(x) x$status_code,
    .package = "httr",
    .env = env
  )
  seen
}

test_that(".read_hadex3_nc reads annual file, converts longitudes, drops fill", {
  f <- tempfile(fileext = ".nc")
  hadex_fx_write_nc(f, "TXx", "annual")
  df <- varunayan:::.read_hadex3_nc(f, "TXx", "annual")
  expect_equal(names(df), c("year", "latitude", "longitude", "value", "index"))
  expect_equal(nrow(df), 17L)
  expect_setequal(unique(df$longitude), c(73.125, 75, -90))
  expect_setequal(unique(df$year), c(1981L, 1982L, 2010L))
  expect_equal(unique(df$index), "TXx")
  v <- df$value[df$year == 2010 & df$longitude == -90 & df$latitude == 20]
  expect_equal(v, hadex_fx_value(3, 2, 3))
  expect_false(any(df$year == 1981 & df$longitude == 73.125 & df$latitude == 18.75))
})

test_that(".read_hadex3_nc reads monthly file", {
  f <- tempfile(fileext = ".nc")
  # months since 1901-01: 960 = 1981-01, 961 = 1981-02, 1307 = 2009-12
  hadex_fx_write_nc(f, "Rx1day", "monthly", times = c(960, 961, 1307))
  df <- varunayan:::.read_hadex3_nc(f, "Rx1day", "monthly")
  expect_equal(names(df), c("year", "month", "latitude", "longitude", "value", "index"))
  expect_setequal(paste(df$year, df$month), c("1981 1", "1981 2", "2009 12"))
  v <- df$value[df$year == 1981 & df$month == 2 & df$longitude == 75 & df$latitude == 18.75]
  expect_equal(v, hadex_fx_value(2, 1, 2))
})

test_that(".read_hadex3_nc errors when expected variable missing", {
  f <- tempfile(fileext = ".nc")
  hadex_fx_write_nc(f, "TXx", "monthly", times = c(0, 1))
  expect_error(varunayan:::.read_hadex3_nc(f, "TXx", "annual"), "Variable 'Ann' not found in NetCDF. Available: TXx")
})

test_that(".parse_hadex3_years / months cover remaining branches", {
  expect_equal(varunayan:::.parse_hadex3_years(c(1901, 1902.2), "years"), c(1901L, 1902L))
  expect_equal(varunayan:::.parse_hadex3_years(c(5, 6), "unknown"), c(5L, 6L))
  ym <- varunayan:::.parse_hadex3_months(c(0, 31), "days since 2000-01-01")
  expect_equal(ym$year, c(2000L, 2000L))
  expect_equal(ym$month, c(1L, 2L))
  expect_error(varunayan:::.parse_hadex3_months(1, "years"), "Unrecognised time units")
})

test_that(".expand_hadex3_annual and _monthly honour fill values", {
  vals <- array(c(1, -99.9, NA, 4), dim = c(2, 1, 2))
  ann <- varunayan:::.expand_hadex3_annual(vals, lat = 10, lon = c(70, 71), years = c(2000L, 2001L), fill_val = -99.9)
  expect_equal(ann$value, c(1, 4))
  expect_equal(ann$year, c(2000L, 2001L))
  expect_equal(ann$longitude, c(70, 71))

  mon <- varunayan:::.expand_hadex3_monthly(vals,
    lat = 10, lon = c(70, 71),
    year_months = data.frame(year = c(2000L, 2000L), month = c(1L, 2L)), fill_val = NULL
  )
  expect_equal(mon$value, c(1, -99.9, 4))
  expect_equal(mon$month, c(1L, 1L, 2L))
})

test_that(".validate_hadex3_inputs returns matched frequency and checks order", {
  expect_equal(varunayan:::.validate_hadex3_inputs("TX90p", "annual", "81-10", 1981, 2010), "annual")
  expect_equal(varunayan:::.validate_hadex3_inputs("TXx", "monthly", "61-90", 1981, 2010), "monthly")
  expect_error(varunayan:::.validate_hadex3_inputs("TXx", "annual", "61-90", 2010, 1981), "start_year must be")
})

test_that(".download_hadex3_file downloads and decompresses", {
  src <- tempfile(fileext = ".nc")
  hadex_fx_write_nc(src)
  seen <- hadex_fx_mock_get(src)
  out_dir <- tempfile("hx")
  dir.create(out_dir)
  nc <- suppressMessages(varunayan:::.download_hadex3_file("TXx", "annual", "61-90", out_dir))
  expect_equal(nc, file.path(out_dir, "HadEX3_TXx_1901-2018_ADW_61-90_1.25x1.875deg.nc"))
  expect_true(file.exists(nc))
  expect_false(file.exists(paste0(nc, ".gz")))
  expect_equal(unname(tools::md5sum(nc)), unname(tools::md5sum(src)))
  expect_match(seen$urls, "HadEX3_TXx_1901-2018_ADW_61-90")
})

test_that(".download_hadex3_file error branches", {
  out_dir <- tempfile("hx")
  dir.create(out_dir)
  hadex_fx_mock_get(tempfile(), status = 404L)
  expect_error(
    suppressMessages(varunayan:::.download_hadex3_file("TXx", "monthly", "61-90", out_dir)),
    "HTTP 404 downloading HadEX3 TXx"
  )
  hadex_fx_mock_get(tempfile(), empty = TRUE)
  expect_error(
    suppressMessages(varunayan:::.download_hadex3_file("TXx", "monthly", "61-90", out_dir)),
    "Downloaded file is empty or missing"
  )
  local_mocked_bindings(GET = function(...) stop("dns"), .package = "httr")
  expect_error(
    suppressMessages(varunayan:::.download_hadex3_file("TXx", "monthly", "61-90", out_dir)),
    "Download failed: dns"
  )
})

test_that(".fetch_hadex3 saves to (mocked) cache when enabled", {
  cache <- imd_fx_local_cache()
  src <- tempfile(fileext = ".nc")
  hadex_fx_write_nc(src)
  hadex_fx_mock_get(src)
  out_dir <- tempfile("hx")
  dir.create(out_dir)
  df <- suppressMessages(varunayan:::.fetch_hadex3("TXx", "annual", "61-90", TRUE, out_dir))
  expect_equal(nrow(df), 17L)
  cached <- list.files(cache, full.names = TRUE)
  expect_length(cached, 1L)
  expect_equal(readRDS(cached), df)
  # decompressed nc removed on exit
  expect_length(list.files(out_dir), 0L)
})

test_that("hadex3_bbox annual end-to-end", {
  imd_fx_local_cache()
  src <- tempfile(fileext = ".nc")
  hadex_fx_write_nc(src)
  hadex_fx_mock_get(src)
  out <- suppressMessages(hadex3_bbox(
    "TXx", 1981, 1982,
    north = 21, south = 18, east = 76, west = 72,
    output_dir = tempfile("hx"), use_cache = FALSE
  ))
  # 2 lons x 2 lats x 2 years minus one fill
  expect_equal(nrow(out), 7L)
  expect_setequal(unique(out$longitude), c(73.125, 75))
  expect_true(all(out$year %in% c(1981, 1982)))
  expect_equal(out$value[out$year == 1982 & out$longitude == 75 & out$latitude == 20], hadex_fx_value(2, 2, 2))
})

test_that("hadex3_bbox monthly end-to-end with western hemisphere longitudes", {
  imd_fx_local_cache()
  src <- tempfile(fileext = ".nc")
  hadex_fx_write_nc(src, "Rx1day", "monthly", times = c(960, 961, 1307))
  seen <- hadex_fx_mock_get(src)
  out <- suppressMessages(hadex3_bbox(
    "Rx1day", 2009, 2009,
    north = 21, south = 18, east = -80, west = -100,
    frequency = "monthly", output_dir = tempfile("hx"), use_cache = FALSE
  ))
  expect_match(seen$urls, "HadEX3_Rx1day_MON\\.nc\\.gz$")
  expect_equal(nrow(out), 2L)
  expect_true(all(out$longitude == -90 & out$month == 12))
  expect_equal(sort(out$value), sort(c(hadex_fx_value(3, 1, 3), hadex_fx_value(3, 2, 3))))
})

test_that("hadex3_geojson end-to-end uses polygon", {
  imd_fx_local_cache()
  src <- tempfile(fileext = ".nc")
  hadex_fx_write_nc(src)
  hadex_fx_mock_get(src)
  gj <- tempfile(fileext = ".geojson")
  imd_fx_write_geojson(gj, 74, 19, 76, 21)
  out <- suppressMessages(hadex3_geojson(
    "TXx", 2010, 2010, gj,
    output_dir = tempfile("hx"), use_cache = FALSE
  ))
  expect_equal(nrow(out), 1L)
  expect_equal(out$longitude, 75)
  expect_equal(out$latitude, 20)
  expect_equal(out$value, hadex_fx_value(2, 2, 3))
  expect_equal(out$index, "TXx")

  gj2 <- tempfile(fileext = ".geojson")
  imd_fx_write_geojson(gj2, 0, 0, 1, 1)
  out2 <- suppressMessages(hadex3_geojson(
    "TXx", 2010, 2010, gj2,
    output_dir = tempfile("hx"), use_cache = FALSE
  ))
  expect_equal(nrow(out2), 0L)
})
