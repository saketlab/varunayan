imd_fx_local_cache <- function(env = parent.frame()) era5_local_cache(env)

days_in_year <- function(year) if (is_leap_year(year)) 366L else 365L

# IMD 1.0 degree temperature grid: lon 67.5..97.5, lat 7.5..37.5 (31 x 31).
imd_fx_temp_lons <- function() seq(67.5, 97.5, by = 1)
imd_fx_temp_lats <- function() seq(7.5, 37.5, by = 1)

# IMD .grd: little-endian float32, lon fastest, then lat, then day; unlisted cells are 99.9 (missing)
imd_fx_write_temperature <- function(path, year,
                                     cells = data.frame(
                                       lon = c(72.5, 73.5),
                                       lat = c(19.5, 19.5),
                                       base = c(20, 30)
                                     ),
                                     n_days = NULL) {
  lons <- imd_fx_temp_lons()
  lats <- imd_fx_temp_lats()
  if (is.null(n_days)) n_days <- days_in_year(year)
  arr <- array(99.9, dim = c(length(lons), length(lats), n_days))
  for (i in seq_len(nrow(cells))) {
    ilon <- match(cells$lon[i], lons)
    ilat <- match(cells$lat[i], lats)
    arr[ilon, ilat, ] <- cells$base[i] + seq_len(n_days) / 10
  }
  con <- file(path, "wb")
  on.exit(close(con), add = TRUE)
  writeBin(as.numeric(arr), con, size = 4, endian = "little")
  invisible(path)
}

# rf = 100 * lon_i + 10 * lat_i + day; cell (1, 1) is -999 (missing) throughout
imd_fx_write_rainfall <- function(path, year,
                                  lons = c(72.25, 72.5, 72.75),
                                  lats = c(19.0, 19.25)) {
  n_days <- days_in_year(year)
  dim_lon <- ncdf4::ncdim_def("lon", "degrees_east", lons)
  dim_lat <- ncdf4::ncdim_def("lat", "degrees_north", lats)
  dim_time <- ncdf4::ncdim_def(
    "time", sprintf("days since %d-01-01", year), seq_len(n_days) - 1L,
    calendar = "standard"
  )
  var_rf <- ncdf4::ncvar_def("rf", "mm", list(dim_lon, dim_lat, dim_time),
    missval = -999, prec = "float"
  )
  nc <- ncdf4::nc_create(path, list(var_rf))
  on.exit(ncdf4::nc_close(nc), add = TRUE)
  arr <- array(NA_real_, dim = c(length(lons), length(lats), n_days))
  for (i in seq_along(lons)) {
    for (j in seq_along(lats)) {
      arr[i, j, ] <- 100 * i + 10 * j + seq_len(n_days)
    }
  }
  arr[1, 1, ] <- -999
  ncdf4::ncvar_put(nc, var_rf, arr)
  invisible(path)
}

# Expected rainfall value for the rainfall fixture.
imd_fx_rain_value <- function(lon_index, lat_index, day_index) {
  100 * lon_index + 10 * lat_index + day_index
}

# Write a polygon GeoJSON covering the given extent.
imd_fx_write_geojson <- function(path, xmin, ymin, xmax, ymax) {
  bb <- sf::st_bbox(c(xmin = xmin, ymin = ymin, xmax = xmax, ymax = ymax),
    crs = sf::st_crs(4326)
  )
  sf::st_write(sf::st_as_sf(sf::st_as_sfc(bb)), path,
    driver = "GeoJSON", quiet = TRUE
  )
  invisible(path)
}

# Fake httr response object for download_imd_year tests.
imd_fx_response <- function(status = 200L, content_type = "application/octet-stream",
                            body = as.raw(1:10)) {
  structure(
    list(status = status, content_type = content_type, body = body),
    class = "imd_fx_response"
  )
}

# CRU TS: value = lon_i * 100 + lat_i * 10 + t; cell (1, 1) holds the fill value at t = 1
cru_fx_write_nc <- function(path, variable = "tmp",
                            lons = c(72.25, 72.75, 80.25),
                            lats = c(18.25, 18.75),
                            dates = as.Date(c("1981-01-16", "1981-02-15", "1982-01-16")),
                            time_units = "days since 1900-1-1") {
  base <- as.Date("1900-01-01")
  tvals <- as.numeric(dates - base)
  dim_lon <- ncdf4::ncdim_def("lon", "degrees_east", lons)
  dim_lat <- ncdf4::ncdim_def("lat", "degrees_north", lats)
  dim_time <- ncdf4::ncdim_def("time", time_units, tvals, calendar = "gregorian")
  fill <- 9.96921e36
  v <- ncdf4::ncvar_def(variable, "degC", list(dim_lon, dim_lat, dim_time),
    missval = fill, prec = "float"
  )
  stn <- ncdf4::ncvar_def("stn", "", list(dim_lon, dim_lat, dim_time),
    missval = -999L, prec = "integer"
  )
  nc <- ncdf4::nc_create(path, list(v, stn))
  on.exit(ncdf4::nc_close(nc), add = TRUE)
  arr <- array(NA_real_, dim = c(length(lons), length(lats), length(tvals)))
  for (i in seq_along(lons)) {
    for (j in seq_along(lats)) {
      arr[i, j, ] <- i * 100 + j * 10 + seq_along(tvals)
    }
  }
  arr[1, 1, 1] <- NA
  ncdf4::ncvar_put(nc, v, arr)
  ncdf4::ncvar_put(nc, stn, array(1L, dim = dim(arr)))
  invisible(path)
}

cru_fx_value <- function(lon_i, lat_i, t) lon_i * 100 + lat_i * 10 + t

cru_fx_gzip <- function(src, gz_path) {
  con_out <- gzfile(gz_path, "wb")
  on.exit(close(con_out), add = TRUE)
  writeBin(readBin(src, "raw", n = file.size(src)), con_out)
  invisible(gz_path)
}

# HadEX3: longitude 0-360; annual files use variable Ann in years, monthly use the index name in months
# value = lon_i*100 + lat_i*10 + t ; cell (1,1,1) = fill (-99.9).
hadex_fx_write_nc <- function(path, index = "TXx", frequency = "annual",
                              lons = c(73.125, 75.0, 270.0),
                              lats = c(18.75, 20.0),
                              times = c(1981, 1982, 2010),
                              time_units = NULL) {
  if (is.null(time_units)) {
    time_units <- if (frequency == "annual") "years" else "months since 1901-01-01"
  }
  var_name <- if (frequency == "annual") "Ann" else index
  dim_lon <- ncdf4::ncdim_def("longitude", "degrees_east", lons)
  dim_lat <- ncdf4::ncdim_def("latitude", "degrees_north", lats)
  dim_time <- ncdf4::ncdim_def("time", time_units, times)
  fill <- -99.9
  v <- ncdf4::ncvar_def(var_name, "degC", list(dim_lon, dim_lat, dim_time),
    missval = fill, prec = "double"
  )
  nc <- ncdf4::nc_create(path, list(v))
  on.exit(ncdf4::nc_close(nc), add = TRUE)
  arr <- array(NA_real_, dim = c(length(lons), length(lats), length(times)))
  for (i in seq_along(lons)) {
    for (j in seq_along(lats)) {
      arr[i, j, ] <- i * 100 + j * 10 + seq_along(times)
    }
  }
  arr[1, 1, 1] <- NA
  ncdf4::ncvar_put(nc, v, arr)
  invisible(path)
}

hadex_fx_value <- function(lon_i, lat_i, t) lon_i * 100 + lat_i * 10 + t

# assert some message matches pattern
imd_fx_expect_msg <- function(expr, pattern) {
  msgs <- testthat::capture_messages(val <- expr)
  testthat::expect_true(any(grepl(pattern, msgs)), info = paste(msgs, collapse = ""))
  invisible(val)
}

# Mock download_imd_temperature() to write one fixture file per year.
imd_fx_mock_temp_download <- function(writer = imd_fx_write_temperature, env = parent.frame()) {
  local_mocked_bindings(
    download_imd_temperature = function(start_year, end_year, var_type, output_dir, use_cache) {
      dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
      vapply(start_year:end_year, function(y) {
        f <- file.path(output_dir, sprintf("imd_%s_1.0_%d.grd", var_type, y))
        writer(f, y)
        f
      }, character(1))
    },
    .env = env
  )
}

skip_live_imd <- function() {
  skip_on_cran()
  skip_if_not(identical(Sys.getenv("VARUNAYAN_LIVE_TESTS"), "true"), "set VARUNAYAN_LIVE_TESTS=true")
  skip_if_offline("imdpune.gov.in")
}
