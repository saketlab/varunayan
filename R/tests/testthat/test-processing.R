# Tests for R/processing.R (NetCDF reading, filtering, aggregation, chunking)

test_that("process_netcdf_to_dataframe reads new CDS layout (valid_time)", {
  f <- withr::local_tempfile(fileext = ".nc")
  era5_make_nc(f, vars = list(
    t2m = era5_default_value,
    tp = function(lon, lat, tidx) tidx / 1000
  ))

  df <- suppressMessages(process_netcdf_to_dataframe(f))

  expect_s3_class(df, "data.frame")
  expect_named(df, c("datetime", "latitude", "longitude", "variable", "value"))
  # 3 lon x 2 lat x 2 times x 2 vars; metadata var number is excluded
  expect_equal(nrow(df), 24)
  expect_setequal(unique(df$variable), c("t2m", "tp"))
  expect_false("number" %in% df$variable)
  expect_s3_class(df$datetime, "POSIXct")
  expect_equal(
    sort(unique(format(df$datetime, "%Y-%m-%d %H:%M", tz = "UTC"))),
    c("2023-01-01 00:00", "2023-01-01 12:00")
  )

  # Values must be attached to the correct (lon, lat, time) cell
  cell <- df[df$variable == "t2m" & df$latitude == 19.75 & df$longitude == 77.5 &
    format(df$datetime, "%H", tz = "UTC") == "12", ]
  expect_equal(nrow(cell), 1)
  expect_equal(cell$value, 280 + 19.75 + 7.75 + 2)

  tp <- df[df$variable == "tp", ]
  expect_equal(sort(unique(tp$value)), c(0.001, 0.002))
})

test_that("process_netcdf_to_dataframe reads legacy layout (time, hours since 1900)", {
  f <- withr::local_tempfile(fileext = ".nc")
  times <- as.POSIXct(c("2020-06-01 00:00", "2020-06-02 00:00", "2020-06-03 00:00"), tz = "UTC")
  era5_make_nc(f,
    times = times, time_name = "time",
    time_units = "hours since 1900-01-01 00:00:00.0", metadata = FALSE
  )

  df <- suppressMessages(process_netcdf_to_dataframe(f))
  expect_equal(nrow(df), 3 * 2 * 3)
  expect_equal(sort(unique(as.Date(df$datetime))), as.Date(times))
})

test_that("process_netcdf_to_dataframe handles a degenerate pressure_level dim", {
  f <- withr::local_tempfile(fileext = ".nc")
  era5_make_nc(f, vars = list(t = era5_default_value), plevel = 850)
  df <- suppressMessages(process_netcdf_to_dataframe(f))
  expect_equal(nrow(df), 12)
  expect_equal(unique(df$variable), "t")
})

test_that("process_netcdf_to_dataframe drops rows with missing values", {
  f <- withr::local_tempfile(fileext = ".nc")
  era5_make_nc(f, vars = list(t2m = function(lon, lat, tidx) {
    ifelse(lon == 77 & lat == 20, NA, 300)
  }))
  df <- suppressMessages(process_netcdf_to_dataframe(f))
  expect_equal(nrow(df), 10)
  expect_false(any(df$latitude == 20 & df$longitude == 77))
})

test_that("process_netcdf_to_dataframe errors on missing file", {
  expect_error(
    process_netcdf_to_dataframe(file.path(tempdir(), "does_not_exist.nc")),
    "Cannot find the NetCDF file"
  )
})

test_that(".read_ncdf4_fast errors without lat/lon dims or data variables", {
  f <- withr::local_tempfile(fileext = ".nc")
  dx <- ncdf4::ncdim_def("x", "m", 1:3)
  nc <- ncdf4::nc_create(f, list(ncdf4::ncvar_def("v", "1", list(dx))))
  ncdf4::ncvar_put(nc, "v", 1:3)
  ncdf4::nc_close(nc)
  expect_error(.read_ncdf4_fast(f), "Cannot find the latitude/longitude dimensions")

  f2 <- withr::local_tempfile(fileext = ".nc")
  dlon <- ncdf4::ncdim_def("longitude", "degrees_east", c(1, 2))
  dlat <- ncdf4::ncdim_def("latitude", "degrees_north", c(3, 4))
  nc <- ncdf4::nc_create(f2, list(ncdf4::ncvar_def("number", "1", list(dlon, dlat))))
  ncdf4::ncvar_put(nc, "number", 1:4)
  ncdf4::nc_close(nc)
  expect_error(.read_ncdf4_fast(f2), "Cannot find data variables")
})

test_that(".read_ncdf4_fast without time dim uses a fixed timestamp", {
  f <- withr::local_tempfile(fileext = ".nc")
  dlon <- ncdf4::ncdim_def("lon", "degrees_east", c(70, 71))
  dlat <- ncdf4::ncdim_def("lat", "degrees_north", c(10, 11, 12))
  nc <- ncdf4::nc_create(f, list(ncdf4::ncvar_def("z", "m", list(dlon, dlat))))
  ncdf4::ncvar_put(nc, "z", 1:6)
  ncdf4::nc_close(nc)

  df <- .read_ncdf4_fast(f)
  expect_equal(nrow(df), 6)
  expect_equal(unique(df$datetime), as.POSIXct("2023-01-01 12:00:00", tz = "UTC"))
  # column-major: lon varies fastest
  expect_equal(df$value[df$longitude == 71 & df$latitude == 12], 6)
  expect_equal(df$value[df$longitude == 70 & df$latitude == 11], 3)
})

test_that("process_netcdf_to_dataframe falls back to stars reader", {
  f <- withr::local_tempfile(fileext = ".nc")
  era5_make_nc(f, vars = list(
    t2m = era5_default_value,
    tp = function(lon, lat, tidx) tidx / 1000
  ))
  local_mocked_bindings(.read_ncdf4_fast = function(netcdf_file) stop("boom"))

  suppressMessages(expect_message(
    df <- process_netcdf_to_dataframe(f),
    "The function will use stars"
  ))
  expect_equal(nrow(df), 24)
  expect_true(all(c("datetime", "latitude", "longitude", "variable", "value") %in% names(df)))
  expect_setequal(unique(df$variable), c("t2m", "tp"))
  cell <- df[df$variable == "t2m" & df$latitude == 20 & df$longitude == 77 &
    format(df$datetime, "%H", tz = "UTC") == "00", ]
  expect_equal(as.numeric(cell$value), 280 + 20 + 7.7 + 1)
})

test_that(".read_ncdf_stars_fallback handles a single variable", {
  f <- withr::local_tempfile(fileext = ".nc")
  era5_make_nc(f)
  df <- suppressMessages(suppressWarnings(.read_ncdf_stars_fallback(f)))
  expect_equal(names(df)[1:5], c("datetime", "latitude", "longitude", "variable", "value"))
  expect_equal(unique(df$variable), "t2m")
  expect_equal(nrow(df), 12)
})

test_that(".parse_nc_time honours the units attribute", {
  expect_equal(
    .parse_nc_time(c(0, 3600), "seconds since 1970-01-01"),
    as.POSIXct(c("1970-01-01 00:00:00", "1970-01-01 01:00:00"), tz = "UTC")
  )
  expect_equal(
    .parse_nc_time(c(1, 2), "minutes since 2000-01-01"),
    as.POSIXct(c("2000-01-01 00:01:00", "2000-01-01 00:02:00"), tz = "UTC")
  )
  expect_equal(
    .parse_nc_time(1, "hours since 1900-01-01 00:00:00.0"),
    as.POSIXct("1900-01-01 01:00:00", tz = "UTC")
  )
  expect_equal(
    .parse_nc_time(c(1, 2), "days since 2000-01-01 00:00:00"),
    as.POSIXct(c("2000-01-02", "2000-01-03"), tz = "UTC")
  )
})

test_that(".parse_nc_time heuristics without units", {
  # Plausible epoch seconds
  expect_equal(
    .parse_nc_time(1672531200),
    as.POSIXct("2023-01-01", tz = "UTC")
  )
  # Unknown unit falls through to the heuristic list
  expect_s3_class(.parse_nc_time(c(1, 2), "fortnights since 2000-01-01"), "POSIXct")
})

test_that(".parse_nc_time falls back to sequential dates with a warning", {
  expect_warning(
    res <- .parse_nc_time(c(5e12, 1e12, 5e12)),
    "sequential dates as a fallback"
  )
  expect_equal(
    res,
    as.POSIXct(c("2023-01-02", "2023-01-01", "2023-01-02"), tz = "UTC")
  )
})

test_that("filter_netcdf_by_bbox keeps only points inside the box", {
  f <- withr::local_tempfile(fileext = ".nc")
  era5_make_nc(f)
  df <- suppressMessages(filter_netcdf_by_bbox(f, north = 20, south = 19.9, east = 77.3, west = 77))
  expect_equal(nrow(df), 4) # 2 lons x 1 lat x 2 times
  expect_true(all(df$latitude == 20))
  expect_setequal(unique(df$longitude), c(77, 77.25))

  none <- suppressMessages(filter_netcdf_by_bbox(f, north = 10, south = 5, east = 10, west = 5))
  expect_equal(nrow(none), 0)
})

test_that("filter_dataframe_by_geojson keeps points inside the polygon", {
  f <- withr::local_tempfile(fileext = ".nc")
  era5_make_nc(f)
  df <- suppressMessages(process_netcdf_to_dataframe(f))
  gj <- era5_make_geojson(77.1, 77.6, 19.9, 20.1)
  on.exit(unlink(gj), add = TRUE)

  out <- suppressMessages(filter_dataframe_by_geojson(df, gj))
  expect_equal(nrow(out), 4)
  expect_true(all(out$latitude == 20))
  expect_setequal(unique(out$longitude), c(77.25, 77.5))
  expect_true(all(c("datetime", "variable", "value") %in% names(out)))
})

test_that("filter_dataframe_by_geojson warns when nothing in bbox", {
  df <- data.frame(
    datetime = as.POSIXct("2023-01-01", tz = "UTC"),
    latitude = 20, longitude = 77, variable = "t2m", value = 1
  )
  gj <- era5_make_geojson(0, 1, 0, 1)
  on.exit(unlink(gj), add = TRUE)
  expect_warning(
    out <- suppressMessages(filter_dataframe_by_geojson(df, gj)),
    "No points are in the bounding box"
  )
  expect_equal(nrow(out), 0)
})

test_that("geojson filters error when the file is missing", {
  missing <- file.path(tempdir(), "no_such_region.geojson")
  expect_error(
    suppressMessages(filter_dataframe_by_geojson(data.frame(latitude = 1, longitude = 1), missing)),
    "Cannot find the GeoJSON file"
  )
  expect_error(filter_netcdf_by_geojson("x.nc", missing), "Cannot find the GeoJSON file")
})

test_that("filter_netcdf_by_geojson composes reading and filtering", {
  f <- withr::local_tempfile(fileext = ".nc")
  era5_make_nc(f)
  gj <- era5_make_geojson(76.9, 77.1, 19.6, 20.1)
  on.exit(unlink(gj), add = TRUE)
  out <- suppressMessages(filter_netcdf_by_geojson(f, gj))
  expect_equal(nrow(out), 4) # lon 77, both lats, 2 times
  expect_true(all(out$longitude == 77))
})

test_that("extract_point_data returns the nearest grid cell time series", {
  f <- withr::local_tempfile(fileext = ".nc")
  era5_make_nc(f)
  suppressMessages(expect_message(
    pt <- extract_point_data(f, target_lat = 19.8, target_lon = 77.4),
    "nearest grid point at \\(19.75, 77.5\\)"
  ))
  expect_equal(nrow(pt), 2)
  expect_true(all(pt$latitude == 19.75 & pt$longitude == 77.5))
  expect_equal(sort(pt$value), 280 + 19.75 + 7.75 + c(1, 2))
})

era5_hourly_df <- function() {
  times <- as.POSIXct("2023-01-30 00:00", tz = "UTC") + 3600 * 12 * (0:7) # 4 days, 2/day
  data.frame(
    datetime = rep(times, each = 2),
    latitude = 20,
    longitude = rep(c(77, 78), times = length(times)),
    variable = "2m_temperature",
    value = seq_len(2 * length(times)),
    stringsAsFactors = FALSE
  )
}

test_that("aggregate_by_frequency computes daily means per cell", {
  df <- era5_hourly_df()
  out <- aggregate_by_frequency(df, "daily")
  expect_setequal(names(out), c("datetime", "latitude", "longitude", "variable", "value"))
  expect_equal(nrow(out), 4 * 2)
  # Jan 30 at lon 77: rows 1 and 3 -> mean(1, 3) = 2
  v <- out$value[as.Date(out$datetime) == as.Date("2023-01-30") & out$longitude == 77]
  expect_equal(v, 2)
  # Feb 2 at lon 78: rows 14 and 16 -> 15
  v <- out$value[as.Date(out$datetime) == as.Date("2023-02-02") & out$longitude == 78]
  expect_equal(v, 15)
  # datetime is the first timestamp in each group
  expect_equal(min(out$datetime), as.POSIXct("2023-01-30 00:00", tz = "UTC"))
})

test_that("aggregate_by_frequency computes monthly and yearly means", {
  df <- era5_hourly_df()
  m <- aggregate_by_frequency(df, "monthly")
  expect_equal(nrow(m), 2 * 2) # Jan, Feb x 2 lons
  # Jan (Jan 30-31) lon 77: values 1,3,5,7 -> 4
  expect_equal(m$value[format(m$datetime, "%m") == "01" & m$longitude == 77], 4)
  # Feb lon 78: values 10,12,14,16 -> 13
  expect_equal(m$value[format(m$datetime, "%m") == "02" & m$longitude == 78], 13)

  y <- aggregate_by_frequency(df, "yearly")
  expect_equal(nrow(y), 2)
  expect_equal(y$value[y$longitude == 77], mean(seq(1, 15, by = 2)))
})

test_that("aggregate_by_frequency verbose path and passthroughs", {
  df <- era5_hourly_df()
  suppressMessages(expect_message(
    aggregate_by_frequency(df, "daily", verbose = TRUE),
    "The temporal aggregation is complete"
  ))
  expect_identical(aggregate_by_frequency(df, "hourly"), df)

  no_dt <- data.frame(a = 1)
  expect_warning(res <- aggregate_by_frequency(no_dt, "daily"), "Cannot find a datetime column")
  expect_identical(res, no_dt)
})

test_that("aggregate_by_frequency ignores NA when averaging", {
  df <- era5_hourly_df()[1:4, ]
  df$value[1] <- NA
  out <- aggregate_by_frequency(df, "daily")
  expect_equal(out$value[out$longitude == 77], 3)
})

test_that("create_temporal_chunks returns a single chunk for short ranges", {
  ch <- create_temporal_chunks("2023-01-01", "2023-01-31", "daily")
  expect_length(ch, 1)
  expect_equal(ch[[1]]$start, as.Date("2023-01-01"))
  expect_equal(ch[[1]]$end, as.Date("2023-01-31"))
})

test_that("create_temporal_chunks splits long ranges contiguously", {
  expect_message(
    ch <- create_temporal_chunks("2023-01-01", "2023-03-15", "daily", max_days_per_chunk = 30),
    "process the range in 3 chunks"
  )
  expect_length(ch, 3)
  starts <- do.call(c, lapply(ch, `[[`, "start"))
  ends <- do.call(c, lapply(ch, `[[`, "end"))
  expect_equal(starts, as.Date(c("2023-01-01", "2023-01-31", "2023-03-02")))
  expect_equal(ends, as.Date(c("2023-01-30", "2023-03-01", "2023-03-15")))
  expect_equal(sum(as.numeric(ends - starts) + 1), 74)
})

test_that("combine_netcdf_files merges, de-duplicates and orders", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  f1 <- file.path(d, "a.nc")
  f2 <- file.path(d, "b.nc")
  f3 <- file.path(d, "c.nc")
  t1 <- as.POSIXct(c("2023-01-01 00:00", "2023-01-01 12:00"), tz = "UTC")
  t2 <- as.POSIXct(c("2023-01-02 00:00"), tz = "UTC")
  era5_make_nc(f1, times = t1)
  era5_make_nc(f2, times = t2)
  era5_make_nc(f3, times = t1) # duplicate of f1

  suppressMessages(expect_message(
    out <- combine_netcdf_files(c(f2, f1, f3, file.path(d, "missing.nc")), verbose = TRUE),
    "Combined data: 18 total data points"
  ))
  expect_equal(nrow(out), 18)
  expect_false(is.unsorted(out$datetime))
  expect_equal(rownames(out), as.character(seq_len(18)))
})

test_that("combine_netcdf_files errors when no files exist", {
  expect_error(
    combine_netcdf_files(file.path(tempdir(), c("nope1.nc", "nope2.nc"))),
    "Cannot find valid NetCDF files"
  )
})

test_that("aggregate_by_frequency sums accumulations and takes max/min where defined", {
  times <- as.POSIXct("2023-01-01", tz = "UTC") + 3600 * 0:2
  df <- data.frame(
    datetime = rep(times, 4), latitude = 0, longitude = 0,
    variable = rep(c("total_precipitation", "mx2t", "mn2t", "2m_temperature"), each = 3),
    value = c(1, 3, 5, 10, 30, 20, 7, 2, 4, 1, 2, 6)
  )
  out <- aggregate_by_frequency(df, "daily")
  got <- stats::setNames(out$value, out$variable)
  expect_equal(got[["total_precipitation"]], 9)
  expect_equal(got[["mx2t"]], 30)
  expect_equal(got[["mn2t"]], 2)
  expect_equal(got[["2m_temperature"]], 3)
})

test_that("aggregate_by_frequency returns NA for all-NA groups without warning", {
  df <- data.frame(
    datetime = as.POSIXct("2023-01-01", tz = "UTC") + 3600 * 0:1,
    latitude = 0, longitude = 0, variable = "mx2t", value = NA_real_
  )
  expect_no_warning(out <- aggregate_by_frequency(df, "daily"))
  expect_true(is.na(out$value))
})
