# era5_ prefix avoids clashes with other helper files

# unique value per (lon, lat, time)
era5_default_value <- function(lon, lat, tidx) {
  280 + lat + lon / 10 + tidx
}

#' Write a small synthetic ERA5-style NetCDF file.
#'
#' Default layout mimics post-2024 CDS output: valid_time in seconds since 1970, number/expver metadata.
#'
#' @param path Output path.
#' @param vars Named list of functions f(lon, lat, tidx) returning values.
#' @param lats,lons Coordinate vectors.
#' @param times POSIXct vector.
#' @param time_name Name of the time dimension ("valid_time" or "time").
#' @param time_units Units string for the time dimension.
#' @param plevel Optional single pressure level; adds a pressure_level dim.
#' @param metadata Whether to add the number metadata variable.
era5_make_nc <- function(path,
                         vars = list(t2m = era5_default_value),
                         lats = c(20, 19.75),
                         lons = c(77, 77.25, 77.5),
                         times = as.POSIXct(
                           c("2023-01-01 00:00:00", "2023-01-01 12:00:00"),
                           tz = "UTC"
                         ),
                         time_name = "valid_time",
                         time_units = "seconds since 1970-01-01",
                         plevel = NULL,
                         metadata = TRUE) {
  origin <- sub("^.*since\\s+", "", time_units)
  unit <- tolower(sub("\\s+since.*$", "", time_units))
  mult <- switch(unit,
    seconds = 1,
    minutes = 60,
    hours = 3600,
    days = 86400
  )
  tvals <- as.numeric(difftime(times, as.POSIXct(origin, tz = "UTC"), units = "secs")) / mult

  dim_lon <- ncdf4::ncdim_def("longitude", "degrees_east", lons)
  dim_lat <- ncdf4::ncdim_def("latitude", "degrees_north", lats)
  dim_time <- ncdf4::ncdim_def(time_name, time_units, tvals)
  dims <- list(dim_lon, dim_lat)
  if (!is.null(plevel)) {
    dims <- c(dims, list(ncdf4::ncdim_def("pressure_level", "hPa", plevel)))
  }
  dims <- c(dims, list(dim_time))

  var_defs <- lapply(names(vars), function(v) {
    ncdf4::ncvar_def(v, "unit", dims, missval = -9999, prec = "double")
  })
  if (metadata) {
    var_defs <- c(var_defs, list(ncdf4::ncvar_def("number", "1", list(), prec = "integer")))
  }

  nc <- ncdf4::nc_create(path, var_defs)
  on.exit(ncdf4::nc_close(nc), add = TRUE)
  grid <- expand.grid(lon = lons, lat = lats, tidx = seq_along(times))
  for (v in names(vars)) {
    vals <- vars[[v]](grid$lon, grid$lat, grid$tidx)
    ncdf4::ncvar_put(nc, v, vals)
  }
  if (metadata) ncdf4::ncvar_put(nc, "number", 0L)
  invisible(path)
}

# skips the test if no zip tool
era5_make_zip <- function(zip_path, files) {
  testthat::skip_if(!nzchar(Sys.which("zip")), "zip utility not available")
  utils::zip(zip_path, files = files, flags = "-j -q")
  zip_path
}

# Fresh temp directory.
era5_tempdir <- function(pattern = "era5") {
  d <- tempfile(pattern)
  dir.create(d, recursive = TRUE)
  d
}

# Redirect the package cache to a throwaway directory for the calling test.
era5_local_cache <- function(env = parent.frame()) {
  # not created yet, so tests see a missing cache until something is saved
  d <- file.path(withr::local_tempdir(.local_envir = env), "cache")
  withr::local_options(varunayan.cache_dir = d, .local_envir = env)
  d
}

# fake ecmwfr::wf_request; writer builds the fixture, calls are logged in log
era5_fake_wf_request <- function(log = new.env(), writer = NULL, ...) {
  log$requests <- list()
  force(writer)
  extra <- list(...)
  function(request, transfer = TRUE, path = tempdir(), ...) {
    log$requests[[length(log$requests) + 1L]] <- request
    out <- file.path(path, request$target)
    if (is.null(writer)) {
      do.call(era5_make_nc, c(list(path = out), extra))
    } else {
      out <- writer(request, out)
    }
    out
  }
}

# A small square GeoJSON polygon written to a temp file.
era5_make_geojson <- function(xmin, xmax, ymin, ymax) {
  path <- tempfile(fileext = ".geojson")
  txt <- sprintf(
    paste0(
      '{"type":"FeatureCollection","features":[{"type":"Feature","properties":{},',
      '"geometry":{"type":"Polygon","coordinates":[[[%s,%s],[%s,%s],[%s,%s],[%s,%s],[%s,%s]]]}}]}'
    ),
    xmin, ymin, xmax, ymin, xmax, ymax, xmin, ymax, xmin, ymin
  )
  writeLines(txt, path)
  path
}

# Windows tempdir() mixes separators; compare resolved paths
expect_same_path <- function(object, expected) {
  expect_equal(normalizePath(object, "/", mustWork = FALSE), normalizePath(expected, "/", mustWork = FALSE))
}
