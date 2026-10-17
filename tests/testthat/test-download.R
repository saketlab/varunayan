test_that("validate_era5_variables works correctly", {
  # Test single-level variables
  valid_single <- c("2m_temperature", "total_precipitation")
  result_single <- validate_era5_variables(valid_single, "single")
  expect_true(all(result_single))
  expect_equal(length(result_single), 2)

  # Test pressure-level variables
  valid_pressure <- c("temperature", "u_component_of_wind")
  result_pressure <- validate_era5_variables(valid_pressure, "pressure")
  expect_true(all(result_pressure))
  expect_equal(length(result_pressure), 2)

  # Test invalid variables
  invalid_vars <- c("invalid_variable", "another_invalid")
  result_invalid <- validate_era5_variables(invalid_vars, "single")
  expect_false(any(result_invalid))
  expect_equal(length(result_invalid), 2)

  # Test mixed valid/invalid
  mixed_vars <- c("2m_temperature", "invalid_variable")
  result_mixed <- validate_era5_variables(mixed_vars, "single")
  expect_true(result_mixed[1])
  expect_false(result_mixed[2])
})

test_that("validate_era5_variables validates dataset_type", {
  expect_error(
    validate_era5_variables(c("temperature"), "invalid"),
    "Invalid dataset_type"
  )
})

test_that("get_single_level_variable_names returns character vector", {
  vars <- get_single_level_variable_names()

  expect_type(vars, "character")
  expect_true(length(vars) > 0)

  # Check for some expected variables
  expect_true("2m_temperature" %in% vars)
  expect_true("total_precipitation" %in% vars)
  expect_true("10m_u_component_of_wind" %in% vars)
})

test_that("get_pressure_level_variable_names returns character vector", {
  vars <- get_pressure_level_variable_names()

  expect_type(vars, "character")
  expect_true(length(vars) > 0)

  # Check for some expected variables
  expect_true("temperature" %in% vars)
  expect_true("u_component_of_wind" %in% vars)
  expect_true("geopotential" %in% vars)
  expect_true("relative_humidity" %in% vars)
})

test_that("variable name lists don't overlap inappropriately", {
  single_vars <- get_single_level_variable_names()
  pressure_vars <- get_pressure_level_variable_names()

  # There might be some overlap (e.g., both have temperature variables but with different names)
  # But they should be distinct lists
  expect_true(length(single_vars) > 0)
  expect_true(length(pressure_vars) > 0)

  # Check that specific variables are in correct lists
  expect_true("2m_temperature" %in% single_vars)
  expect_false("2m_temperature" %in% pressure_vars)

  expect_true("temperature" %in% pressure_vars)
  expect_false("temperature" %in% single_vars)
})

era5_dl_args <- function(dir, ...) {
  utils::modifyList(list(
    variables = "2m_temperature",
    start_date = "2023-01-01",
    end_date = "2023-01-02",
    area = c(20, 77, 19.75, 77.5),
    output_file = file.path(dir, "out.nc"),
    use_cache = FALSE
  ), list(...))
}

era5_failing_wf_request <- function(msg, log = new.env()) {
  log$n <- 0L
  function(...) {
    log$n <- log$n + 1L
    stop(msg)
  }
}

test_that("signal_if_too_large signals only for size-related errors", {
  expect_error(
    signal_if_too_large("Your request is too large", "2023-01-01", "2023-01-02"),
    class = "cds_request_too_large"
  )
  expect_error(
    signal_if_too_large("exceeds cost limits", "2023-01-01", "2023-01-02"),
    "The CDS request is too large: exceeds cost limits"
  )
  # Generic failure only counts as size-related for long ranges
  expect_error(
    signal_if_too_large("Request has failed", "2020-01-01", "2022-01-01"),
    class = "cds_request_too_large"
  )
  expect_null(signal_if_too_large("Request has failed", "2023-01-01", "2023-02-01"))
  expect_null(signal_if_too_large("network down", "2020-01-01", "2023-01-01"))
})

test_that("setup_cds_credentials uses the explicit key, env var, or cdsapirc", {
  keys <- character()
  local_mocked_bindings(wf_set_key = function(key, ...) {
    keys <<- c(keys, key)
    invisible(TRUE)
  })
  withr::local_envvar(CDS_API_KEY = "")

  expect_true(suppressMessages(setup_cds_credentials(key = "explicit-key")))
  expect_equal(keys, "explicit-key")

  withr::local_envvar(CDS_API_KEY = "env-key")
  suppressMessages(expect_message(setup_cds_credentials(), "CDS_API_KEY environment variable"))
  expect_equal(keys[2], "env-key")

  withr::local_envvar(CDS_API_KEY = "")
  local_mocked_bindings(read_cdsapirc = function(...) list(url = "u", key = "file-key"))
  suppressMessages(setup_cds_credentials())
  expect_equal(keys[3], "file-key")

  local_mocked_bindings(read_cdsapirc = function(...) NULL)
  expect_error(suppressMessages(setup_cds_credentials()), "Cannot find the CDS credentials")
  expect_length(keys, 3)
})

test_that("download_era5_single builds an hourly request and returns the file", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(
    get_cds_credentials = function(...) TRUE,
    wf_request = era5_fake_wf_request(log)
  )

  res <- suppressMessages(do.call(download_era5_single, era5_dl_args(d, retry_attempts = 0)))
  expect_equal(normalizePath(res), normalizePath(file.path(d, "out.nc")))
  expect_true(file.exists(res))

  req <- log$requests[[1]]
  expect_equal(req$dataset_short_name, "reanalysis-era5-single-levels")
  expect_equal(unlist(req$product_type), "reanalysis")
  expect_equal(unlist(req$date), c("2023-01-01", "2023-01-02"))
  expect_equal(unlist(req$time), sprintf("%02d:00", 0:23))
  expect_equal(req$area, c(20, 77, 19.75, 77.5))
  expect_equal(req$target, "out.nc")
  expect_equal(unlist(req$variable), "2m_temperature")
})

test_that("download_era5_single uses 12:00 for daily and monthly-means product", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(
    get_cds_credentials = function(...) TRUE,
    wf_request = era5_fake_wf_request(log)
  )

  suppressMessages(do.call(download_era5_single, era5_dl_args(d, frequency = "daily", retry_attempts = 0)))
  expect_equal(unlist(log$requests[[1]]$time), "12:00")

  suppressMessages(do.call(download_era5_single, era5_dl_args(d,
    frequency = "monthly", start_date = "2022-11-01", end_date = "2023-02-28",
    area = NULL
  )))
  req <- log$requests[[2]]
  expect_equal(req$dataset_short_name, "reanalysis-era5-single-levels-monthly-means")
  expect_equal(unlist(req$product_type), "monthly_averaged_reanalysis")
  expect_equal(unlist(req$year), c("2022", "2023"))
  expect_equal(unlist(req$month), c("11", "12", "01", "02"))
  expect_null(req$area)
  expect_null(req$date)

  # max/min temperature are not available as monthly means
  suppressMessages(do.call(download_era5_single, era5_dl_args(d,
    variables = "maximum_2m_temperature_since_previous_post_processing",
    frequency = "monthly", retry_attempts = 0
  )))
  expect_equal(log$requests[[3]]$dataset_short_name, "reanalysis-era5-single-levels")
})

test_that("download_era5_single extracts a zipped download", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  src <- era5_tempdir("src")
  on.exit(unlink(src, recursive = TRUE), add = TRUE)
  era5_make_nc(file.path(src, "data_stream-oper.nc"))
  era5_make_zip(file.path(src, "payload.zip"), file.path(src, "data_stream-oper.nc"))

  local_mocked_bindings(
    get_cds_credentials = function(...) TRUE,
    wf_request = function(request, transfer, path, ...) {
      out <- file.path(path, "download.zip")
      file.copy(file.path(src, "payload.zip"), out)
      out
    }
  )
  res <- suppressMessages(do.call(download_era5_single, era5_dl_args(d, retry_attempts = 0)))
  expect_equal(basename(res), "data_stream-oper.nc")
  expect_true(file.exists(res))
  expect_false(file.exists(file.path(d, "download.zip")))
  df <- suppressMessages(process_netcdf_to_dataframe(res))
  expect_equal(nrow(df), 12)
})

test_that("download_era5_single locates the file when wf_request returns no path", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  local_mocked_bindings(
    get_cds_credentials = function(...) TRUE,
    wf_request = function(request, transfer, path, ...) {
      era5_make_nc(file.path(path, request$target))
      file.path(path, "nonexistent.nc")
    }
  )
  res <- suppressMessages(do.call(download_era5_single, era5_dl_args(d, retry_attempts = 0)))
  expect_equal(res, file.path(d, "out.nc"))
})

test_that("download_era5_single errors without credentials", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  local_mocked_bindings(
    get_cds_credentials = function(...) FALSE,
    wf_request = function(...) stop("must not be called")
  )
  expect_error(
    do.call(download_era5_single, era5_dl_args(d)),
    "Cannot find the CDS credentials"
  )
})

test_that("download_era5_single reports authentication failures immediately", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(
    get_cds_credentials = function(...) TRUE,
    wf_request = era5_failing_wf_request("HTTP 401 Unauthorized", log)
  )
  expect_error(
    suppressMessages(do.call(download_era5_single, era5_dl_args(d, retry_attempts = 5))),
    "Authentication failed"
  )
  expect_equal(log$n, 1L)
})

test_that("download_era5_single signals too-large and generic failures", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  local_mocked_bindings(
    get_cds_credentials = function(...) TRUE,
    wf_request = era5_failing_wf_request("the request is too large")
  )
  expect_warning(
    expect_error(
      suppressMessages(do.call(download_era5_single, era5_dl_args(d, retry_attempts = 0))),
      class = "cds_request_too_large"
    ),
    "Download failed on attempt 1"
  )

  local_mocked_bindings(wf_request = era5_failing_wf_request("connection reset"))
  expect_warning(
    expect_error(
      suppressMessages(do.call(download_era5_single, era5_dl_args(d, retry_attempts = 0))),
      "Download failed after 1 attempts: connection reset"
    ),
    "Download failed on attempt 1"
  )

  local_mocked_bindings(wf_request = era5_failing_wf_request("Request timed out"))
  expect_warning(
    expect_error(
      suppressMessages(do.call(download_era5_single, era5_dl_args(d, retry_attempts = 0))),
      "Download failed after 1 attempts"
    ),
    "Timeout on attempt 1"
  )

  local_mocked_bindings(wf_request = era5_failing_wf_request("server busy, queued"))
  expect_warning(
    expect_error(
      suppressMessages(do.call(download_era5_single, era5_dl_args(d, retry_attempts = 0))),
      "Download failed after 1 attempts"
    ),
    "CDS server is busy on attempt 1"
  )
})

test_that("download_era5_single saves to and reuses the cache", {
  era5_local_cache()
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(
    get_cds_credentials = function(...) TRUE,
    wf_request = era5_fake_wf_request(log)
  )
  args <- era5_dl_args(d, use_cache = TRUE, retry_attempts = 0)
  suppressMessages(do.call(download_era5_single, args))
  expect_length(log$requests, 1)
  expect_equal(nrow(suppressMessages(list_cache("era5"))), 1)

  args$output_file <- file.path(d, "second.nc")
  suppressMessages(expect_message(
    res <- do.call(download_era5_single, args),
    "The package uses cached data"
  ))
  expect_length(log$requests, 1)
  expect_true(file.exists(file.path(d, "second.nc")))
  expect_equal(res, file.path(d, "second.nc"))
})

test_that("download_era5_pressure builds the request and caches the result", {
  era5_local_cache()
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  log <- new.env()
  local_mocked_bindings(
    get_cds_credentials = function(...) TRUE,
    wf_request = era5_fake_wf_request(log, vars = list(t = era5_default_value), plevel = 850)
  )
  args <- era5_dl_args(d,
    variables = "temperature", pressure_levels = c("850"),
    frequency = "daily", use_cache = TRUE
  )
  res <- suppressMessages(do.call(download_era5_pressure, args))
  expect_true(file.exists(res))
  req <- log$requests[[1]]
  expect_equal(req$dataset_short_name, "reanalysis-era5-pressure-levels")
  expect_equal(unlist(req$pressure_level), "850")
  expect_equal(unlist(req$time), "12:00")

  args$output_file <- file.path(d, "again.nc")
  msgs <- testthat::capture_messages(do.call(download_era5_pressure, args))
  expect_true(any(grepl("The package uses cached data", msgs)))
  expect_length(log$requests, 1)

  # hourly and monthly time selections
  args$use_cache <- FALSE
  args$frequency <- "hourly"
  suppressMessages(do.call(download_era5_pressure, args))
  expect_equal(unlist(log$requests[[2]]$time), sprintf("%02d:00", 0:23))
  args$frequency <- "monthly"
  suppressMessages(do.call(download_era5_pressure, args))
  expect_equal(unlist(log$requests[[3]]$time), "12:00")
})

test_that("download_era5_pressure maps errors to informative messages", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  args <- era5_dl_args(d, variables = "temperature", pressure_levels = "500")
  local_mocked_bindings(get_cds_credentials = function(...) TRUE)

  run <- function(msg) {
    local_mocked_bindings(wf_request = era5_failing_wf_request(msg), .env = parent.frame())
    suppressMessages(do.call(download_era5_pressure, args))
  }
  expect_error(run("401 Client Error"), "Authentication failed")
  expect_error(run("cost limits exceeded"), class = "cds_request_too_large")
  expect_error(run("Operation timed out"), "Timeout of the request")
  expect_error(run("server is busy"), "The CDS server is busy")
  expect_error(run("weird failure"), "Download failed: weird failure")

  local_mocked_bindings(get_cds_credentials = function(...) FALSE)
  expect_error(do.call(download_era5_pressure, args), "Cannot find the CDS credentials")
})

test_that("extract_zip_to_nc handles single, multiple and empty archives", {
  src <- era5_tempdir("src")
  out <- era5_tempdir("out")
  on.exit(unlink(c(src, out), recursive = TRUE), add = TRUE)
  era5_make_nc(file.path(src, "a.nc"))
  era5_make_nc(file.path(src, "b.nc"), vars = list(tp = function(lon, lat, tidx) tidx))
  writeLines("x", file.path(src, "readme.txt"))

  z1 <- era5_make_zip(file.path(src, "one.zip"), file.path(src, "a.nc"))
  res <- suppressMessages(extract_zip_to_nc(z1, out))
  expect_equal(res, file.path(out, "a.nc"))
  expect_true(file.exists(res))
  expect_false(file.exists(z1))
  expect_false(dir.exists(file.path(out, "extracted")))

  z2 <- era5_make_zip(file.path(src, "two.zip"), file.path(src, c("a.nc", "b.nc")))
  suppressMessages(expect_message(res2 <- extract_zip_to_nc(z2, out), "The package merges 2 NetCDF files"))
  expect_equal(basename(res2), "merged_a.nc")
  df <- suppressMessages(process_netcdf_to_dataframe(res2))
  expect_setequal(unique(df$variable), c("t2m", "tp"))
  expect_equal(sort(unique(df$value[df$variable == "tp"])), c(1, 2))

  z3 <- era5_make_zip(file.path(src, "none.zip"), file.path(src, "readme.txt"))
  expect_error(suppressMessages(extract_zip_to_nc(z3, out)), "The ZIP archive does not contain NetCDF files")
})

test_that("merge_nc_files combines variables and preserves dimensions", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  a <- file.path(d, "a.nc")
  b <- file.path(d, "b.nc")
  era5_make_nc(a)
  era5_make_nc(b, vars = list(tp = function(lon, lat, tidx) lat))
  m <- suppressMessages(merge_nc_files(c(a, b), d))
  expect_equal(m, file.path(d, "merged_a.nc"))

  nc <- ncdf4::nc_open(m)
  on.exit(ncdf4::nc_close(nc), add = TRUE, after = FALSE)
  expect_setequal(names(nc$var), c("t2m", "tp"))
  expect_setequal(names(nc$dim), c("longitude", "latitude", "valid_time"))
  expect_equal(nc$dim$valid_time$units, "seconds since 1970-01-01")
  expect_equal(as.vector(ncdf4::ncvar_get(nc, "tp"))[1:3], c(20, 20, 20))

  # only metadata variables -> error
  e <- file.path(d, "meta.nc")
  dlon <- ncdf4::ncdim_def("longitude", "degrees_east", 1)
  nc2 <- ncdf4::nc_create(e, list(ncdf4::ncvar_def("expver", "1", list(dlon))))
  ncdf4::ncvar_put(nc2, "expver", 1)
  ncdf4::nc_close(nc2)
  expect_error(merge_nc_files(e, d), "The NetCDF files do not contain climate variables")
})

test_that("find_and_extract_download finds output, zip or target files", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  out <- file.path(d, "req.nc")

  expect_error(find_and_extract_download(out, "target.nc"), "Cannot find the downloaded file")

  era5_make_nc(file.path(d, "target.nc"))
  expect_same_path(find_and_extract_download(out, "target.nc"), file.path(d, "target.nc"))

  era5_make_nc(out)
  expect_equal(find_and_extract_download(out, "target.nc"), out)

  file.remove(out)
  src <- era5_tempdir("src")
  on.exit(unlink(src, recursive = TRUE), add = TRUE)
  era5_make_nc(file.path(src, "inner.nc"))
  era5_make_zip(file.path(d, "req.zip"), file.path(src, "inner.nc"))
  res <- suppressMessages(find_and_extract_download(out, "zzz.nc"))
  expect_same_path(res, file.path(d, "inner.nc"))
  expect_false(file.exists(file.path(d, "req.zip")))
})

test_that("validate_era5_variables caches lists per dataset type", {
  rm(list = ls(envir = .varunayan_cache), envir = .varunayan_cache)
  expect_equal(validate_era5_variables(c("geopotential", "2m_temperature"), "pressure"), c(TRUE, FALSE))
  expect_true(exists("valid_vars_pressure", envir = .varunayan_cache))
  # second call served from cache
  expect_equal(validate_era5_variables("vorticity", "pressure"), TRUE)
  expect_equal(validate_era5_variables(character(), "single"), logical())
})

test_that("download_era5_pressure handles zipped and path-less downloads", {
  d <- era5_tempdir()
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  src <- era5_tempdir("src")
  on.exit(unlink(src, recursive = TRUE), add = TRUE)
  era5_make_nc(file.path(src, "pl.nc"), vars = list(t = era5_default_value), plevel = 500)
  era5_make_zip(file.path(src, "pl.zip"), file.path(src, "pl.nc"))
  args <- era5_dl_args(d, variables = "temperature", pressure_levels = "500")

  local_mocked_bindings(
    get_cds_credentials = function(...) TRUE,
    wf_request = function(request, transfer, path, ...) {
      out <- file.path(path, "dl.zip")
      file.copy(file.path(src, "pl.zip"), out)
      out
    }
  )
  res <- suppressMessages(do.call(download_era5_pressure, args))
  expect_same_path(res, file.path(d, "pl.nc"))
  expect_equal(nrow(suppressMessages(process_netcdf_to_dataframe(res))), 12)

  local_mocked_bindings(wf_request = function(request, transfer, path, ...) {
    era5_make_nc(file.path(path, request$target))
    NULL
  })
  res <- suppressMessages(do.call(download_era5_pressure, args))
  expect_equal(res, file.path(d, "out.nc"))
})
