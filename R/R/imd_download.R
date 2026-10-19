.IMD_BASE_URL <- "https://imdpune.gov.in/"
.IMD_RAIN_YEARS <- c(1901L, 2025L)
.IMD_TEMP_YEARS <- c(1951L, 2025L)
.IMD_GRID_URL <- paste0(.IMD_BASE_URL, "cmpg/Griddata/")
# Download form for each dataset: the endpoint it posts to and its field
.IMD_ENDPOINTS <- data.frame(
  dataset = c("rainfall_0.25", "rainfall_1.0", "tmax_1.0", "tmin_1.0"),
  php = c("RF25.php", "rainfallone.php", "maxtemp.php", "mintemp.php"),
  param = c("RF25", "rainone", "maxtemp", "mintemp")
)
.imd_endpoint <- function(dataset) as.list(.IMD_ENDPOINTS[.IMD_ENDPOINTS$dataset == dataset, ])

# imdpune.gov.in drops TLS handshakes in bursts and connects slowly
.IMD_CONNECT_TIMEOUT <- 60
.IMD_RETRIES <- 8L

# retry connection failures and 5xx; any other response goes back to the caller
.imd_request <- function(verb, url, ..., retries = .IMD_RETRIES, timeout_s = 600) {
  for (attempt in seq_len(retries)) {
    if (attempt > 1) Sys.sleep(min(2^(attempt - 1), 30))
    r <- tryCatch(
      verb(url, ..., timeout(timeout_s), config(connecttimeout = .IMD_CONNECT_TIMEOUT)),
      error = function(e) e
    )
    if (!inherits(r, "error") && status_code(r) < 500) {
      return(r)
    }
    msg <- if (inherits(r, "error")) conditionMessage(r) else paste("Server returned status", status_code(r))
    warning(sprintf(fmt = "Attempt %s/%s failed: %s", attempt, retries, msg), call. = FALSE)
  }
  stop("Failed after ", retries, " attempts. Last error: ", msg, call. = FALSE)
}

#' Download IMD gridded rainfall data
#'
#' Downloads daily gridded rainfall data from IMD at the specified resolution.
#'
#' @param start_year Start year.
#' @param end_year End year.
#' @param resolution Spatial resolution: 0.25 or 1.0 degrees.
#' @param output_dir Directory for the downloaded files.
#' @param use_cache If TRUE, use the cached data when it is available (default: TRUE).
#' @return Character vector of the paths to the downloaded files.
#' @export
#' @examplesIf interactive()
#' # Download 0.25 degree rainfall for 2023-2025
#' files <- download_imd_rainfall(
#'   start_year = 2023,
#'   end_year = 2025,
#'   resolution = 0.25
#' )
download_imd_rainfall <- function(start_year, end_year, resolution = 0.25, output_dir = tempdir(), use_cache = TRUE) {
  if (start_year < .IMD_RAIN_YEARS[1] || end_year > .IMD_RAIN_YEARS[2]) {
    stop(sprintf("Rainfall data is available only for the years %d-%d", .IMD_RAIN_YEARS[1], .IMD_RAIN_YEARS[2]))
  }
  if (start_year > end_year) stop("Start year must be <= end year")
  if (!resolution %in% c(0.25, 1.0)) stop("Resolution must be 0.25 or 1.0 degrees")


  endpoint <- .imd_endpoint(paste0("rainfall_", format(resolution, nsmall = 1)))

  message(sprintf(fmt = "IMD rainfall data download started (resolution: %s\u00B0)", resolution))
  message(sprintf(fmt = "Years: %s to %s", start_year, end_year))

  ensure_output_dir(output_dir)


  years <- start_year:end_year
  cached_years <- c()
  missing_years <- c()

  if (use_cache) {
    message("Check of the cache for available data...")
    for (year in years) {
      cache_key <- generate_cache_key(
        source = "imd",
        start_date = paste0(year, "-01-01"),
        end_date = paste0(year, "-12-31"),
        resolution = resolution,
        var_type = "rainfall"
      )
      cached_file <- check_cache(cache_key)
      if (!is.null(cached_file)) {
        cached_years <- c(cached_years, year)
      } else {
        missing_years <- c(missing_years, year)
      }
    }

    if (length(x = cached_years) > 0) {
      message(sprintf(fmt = "Found %s year(s) in cache: %s", length(x = cached_years), paste(cached_years, collapse = ", ")))
    }
    if (length(x = missing_years) > 0) {
      message(sprintf(fmt = "Download is necessary for %s year(s): %s", length(x = missing_years), paste(missing_years, collapse = ", ")))
    }
  } else {
    missing_years <- years
    message(sprintf(fmt = "Cache is disabled. The function will download all %s years.", length(x = missing_years)))
  }


  if (length(x = missing_years) > 0) {
    message("Check of the connection to the IMD server...")
    if (!check_imd_server()) {
      warning("IMD server (", .IMD_BASE_URL, ") does not respond", call. = FALSE)

      if (length(x = cached_years) == length(x = years)) {
        message("All the requested data is in the cache. The function will use only the cached data.")
      } else {
        stop(sprintf(fmt = "Cannot connect to the server, and %s year(s) are not in the cache", length(x = missing_years)))
        message("Possible causes:")
        message(paste("  -", c(
          "The server is temporarily not in operation",
          "Problems with the network connection",
          "A firewall or proxy stops the connection",
          "The server is in maintenance"
        ), collapse = "\n"))
        message("Options:")
        message(paste("  -", c(
          "Try again later, when the server is available",
          sprintf(fmt = "Request only the cached years: %s", paste(cached_years, collapse = ", ")),
          "Use ERA5 data as an alternative"
        ), collapse = "\n"))
        stop("Cannot connect to the IMD server, and some data is not in the cache")
      }
    } else {
      message("The IMD server is available")
    }
  } else {
    message("All the requested data is in the cache. No download is necessary.")
  }


  files <- vapply(years, function(year) {
    output_file <- file.path(output_dir, sprintf(fmt = "imd_rainfall_%s_%d.nc", resolution, year))


    if (use_cache) {
      cache_key <- generate_cache_key(
        source = "imd",
        start_date = paste0(year, "-01-01"),
        end_date = paste0(year, "-12-31"),
        resolution = resolution,
        var_type = "rainfall"
      )

      cached_file <- check_cache(cache_key)
      if (!is.null(cached_file)) {
        message(sprintf(fmt = "Use of cached data for %s: %s", year, basename(path = cached_file)))
        file.copy(cached_file, output_file, overwrite = TRUE)
        return(output_file)
      }
    }

    tryCatch(
      {
        message(sprintf(fmt = "Download of year %s...", year))
        result <- download_imd_year(
          year, endpoint$php, endpoint$param, .IMD_GRID_URL, output_file
        )
        message(sprintf(fmt = "Downloaded %s: %s", year, basename(path = result)))


        if (use_cache) {
          tryCatch(
            {
              save_to_cache(result, cache_key)
            },
            error = function(e) {
              warning(sprintf(fmt = "Cannot save to the cache: %s", e$message), call. = FALSE)
            }
          )
        }

        result
      },
      error = function(e) {
        stop(sprintf(fmt = "Download failed for %s: %s", year, e$message))
        NA_character_
      }
    )
  }, character(1))

  files <- files[!is.na(files)]
  message(sprintf(fmt = "Downloaded %s files", length(x = files)))
  files
}

#' Download IMD gridded temperature data
#'
#' Downloads daily gridded temperature data (maximum or minimum) from IMD.
#' Temperature data is available only at 1.0 degree resolution.
#'
#' @param start_year Start year.
#' @param end_year End year.
#' @param var_type Type of temperature: "tmax" or "tmin".
#' @param output_dir Directory for the downloaded files.
#' @param use_cache If TRUE, use the cached data when it is available (default: TRUE).
#' @return Character vector of the paths to the downloaded files.
#' @export
#' @examplesIf interactive()
#' # Download maximum temperature for 2023-2025
#' files <- download_imd_temperature(
#'   start_year = 2023,
#'   end_year = 2025,
#'   var_type = "tmax"
#' )
download_imd_temperature <- function(start_year, end_year, var_type = "tmax", output_dir = tempdir(), use_cache = TRUE) {
  if (start_year < .IMD_TEMP_YEARS[1] || end_year > .IMD_TEMP_YEARS[2]) {
    stop(sprintf("Temperature data is available only for the years %d-%d", .IMD_TEMP_YEARS[1], .IMD_TEMP_YEARS[2]))
  }
  if (start_year > end_year) stop("Start year must be <= end year")
  if (!var_type %in% c("tmax", "tmin")) stop("var_type must be 'tmax' or 'tmin'")


  endpoint <- .imd_endpoint(paste0(var_type, "_1.0"))

  message(sprintf(fmt = "IMD %s data download started (resolution: 1.0\u00B0)", var_type))
  message(sprintf(fmt = "Years: %s to %s", start_year, end_year))

  ensure_output_dir(output_dir)


  years <- start_year:end_year
  cached_years <- c()
  missing_years <- c()

  if (use_cache) {
    message("Check of the cache for available data...")
    for (year in years) {
      cache_key <- generate_cache_key(
        source = "imd",
        start_date = paste0(year, "-01-01"),
        end_date = paste0(year, "-12-31"),
        resolution = 1.0,
        var_type = var_type
      )
      cached_file <- check_cache(cache_key)
      if (!is.null(cached_file)) {
        cached_years <- c(cached_years, year)
      } else {
        missing_years <- c(missing_years, year)
      }
    }

    if (length(x = cached_years) > 0) {
      message(sprintf(fmt = "Found %s year(s) in cache: %s", length(x = cached_years), paste(cached_years, collapse = ", ")))
    }
    if (length(x = missing_years) > 0) {
      message(sprintf(fmt = "Download is necessary for %s year(s): %s", length(x = missing_years), paste(missing_years, collapse = ", ")))
    }
  } else {
    missing_years <- years
    message(sprintf(fmt = "Cache is disabled. The function will download all %s years.", length(x = missing_years)))
  }


  if (length(x = missing_years) > 0) {
    message("Check of the connection to the IMD server...")
    if (!check_imd_server()) {
      warning("IMD server (", .IMD_BASE_URL, ") does not respond", call. = FALSE)

      if (length(x = cached_years) == length(x = years)) {
        message("All the requested data is in the cache. The function will use only the cached data.")
      } else {
        stop(sprintf(fmt = "Cannot connect to the server, and %s year(s) are not in the cache", length(x = missing_years)))
        message("Possible causes:")
        message(paste("  -", c(
          "The server is temporarily not in operation",
          "Problems with the network connection",
          "A firewall or proxy stops the connection",
          "The server is in maintenance"
        ), collapse = "\n"))
        message("Options:")
        message(paste("  -", c(
          "Try again later, when the server is available",
          sprintf(fmt = "Request only the cached years: %s", paste(cached_years, collapse = ", ")),
          "Use ERA5 data as an alternative"
        ), collapse = "\n"))
        stop("Cannot connect to the IMD server, and some data is not in the cache")
      }
    } else {
      message("The IMD server is available")
    }
  } else {
    message("All the requested data is in the cache. No download is necessary.")
  }


  files <- vapply(years, function(year) {
    output_file <- file.path(output_dir, sprintf(fmt = "imd_%s_1.0_%d.grd", var_type, year))


    if (use_cache) {
      cache_key <- generate_cache_key(
        source = "imd",
        start_date = paste0(year, "-01-01"),
        end_date = paste0(year, "-12-31"),
        resolution = 1.0,
        var_type = var_type
      )

      cached_file <- check_cache(cache_key)
      if (!is.null(cached_file)) {
        message(sprintf(fmt = "Use of cached data for %s: %s", year, basename(path = cached_file)))
        file.copy(cached_file, output_file, overwrite = TRUE)
        return(output_file)
      }
    }

    tryCatch(
      {
        message(sprintf(fmt = "Download of year %s...", year))
        result <- download_imd_year(
          year, endpoint$php, endpoint$param, .IMD_GRID_URL, output_file
        )
        message(sprintf(fmt = "Downloaded %s: %s", year, basename(path = result)))


        if (use_cache) {
          tryCatch(
            {
              save_to_cache(result, cache_key)
            },
            error = function(e) {
              warning(sprintf(fmt = "Cannot save to the cache: %s", e$message), call. = FALSE)
            }
          )
        }

        result
      },
      error = function(e) {
        stop(sprintf(fmt = "Download failed for %s: %s", year, e$message))
        NA_character_
      }
    )
  }, character(1))

  files <- files[!is.na(files)]
  message(sprintf(fmt = "Downloaded %s files", length(x = files)))
  files
}

#' Check the connection to the IMD server
#'
#' @param base_url Base URL for the test.
#' @param timeout Request timeout in seconds.
#' @param retries Attempts before giving up.
#' @return Logical. TRUE if the server is available.
#' @keywords internal
check_imd_server <- function(base_url = .IMD_BASE_URL, timeout = 60, retries = .IMD_RETRIES) {
  tryCatch(
    {
      suppressWarnings(.imd_request(HEAD, base_url, retries = retries, timeout_s = timeout))
      TRUE
    },
    error = function(e) FALSE
  )
}

#' Internal function to download a single year of IMD data
#'
#' Connection failures and server errors are retried; a response without data
#' (another status, an HTML page or an empty body) fails at once.
#'
#' @param year Year to download.
#' @param php_file PHP endpoint file.
#' @param param_name POST parameter name.
#' @param base_url Base URL.
#' @param output_file Path for the downloaded file.
#' @param max_retries Maximum number of attempts.
#' @return Character string. The path to the downloaded file.
#' @keywords internal
download_imd_year <- function(year, php_file, param_name, base_url, output_file, max_retries = .IMD_RETRIES) {
  response <- .imd_request(POST, paste0(base_url, php_file),
    body = setNames(list(as.character(x = year)), param_name), encode = "form",
    retries = max_retries
  )
  if (status_code(response) != 200) stop("Server returned status ", status_code(response))
  if (grepl(pattern = "text/html", headers(response)$`content-type`, ignore.case = TRUE)) {
    stop("Server returned HTML instead of data for ", year)
  }
  writeBin(content(response, "raw"), output_file)
  if (!file.exists(output_file) || file.size(output_file) == 0) stop("Downloaded file is empty or does not exist")
  output_file
}

#' Get IMD grid specifications
#'
#' Returns the grid specifications for an IMD dataset.
#'
#' @param dataset Dataset identifier: "rainfall_0.25",
#'   "rainfall_1.0", "tmax_1.0", "tmin_1.0".
#' @return A list with elements `nlat`, `nlon`, `lat_start`, `lat_end`, `lon_start`, `lon_end`, `resolution` (degrees), `unit`, `missing_value`, `format` and `description`.
#' @export
#' @examples
#' specs <- get_imd_grid_specs("rainfall_0.25")
get_imd_grid_specs <- function(dataset) {
  specs <- list(
    "rainfall_0.25" = list(
      nlat = 129, # Value from the NetCDF file
      nlon = 135, # Value from the NetCDF file
      lat_start = 6.5,
      lat_end = 38.5,
      lon_start = 66.5,
      lon_end = 100.0,
      resolution = 0.25,
      unit = "mm",
      missing_value = -999,
      format = "NetCDF",
      variable_name = "RAINFALL",
      description = "Daily rainfall at 0.25 degree resolution"
    ),
    "rainfall_1.0" = list(
      nlat = 33,
      nlon = 35,
      lat_start = 6.5,
      lat_end = 38.5,
      lon_start = 66.5,
      lon_end = 100.5,
      resolution = 1.0,
      unit = "mm",
      missing_value = -999,
      format = "NetCDF",
      variable_name = "RAINFALL",
      description = "Daily rainfall at 1.0 degree resolution"
    ),
    "tmax_1.0" = list(
      nlat = 31,
      nlon = 31,
      lat_start = 7.5,
      lat_end = 37.5,
      lon_start = 67.5,
      lon_end = 97.5,
      resolution = 1.0,
      unit = "Celsius",
      missing_value = 99.9,
      format = "Binary",
      description = "Daily maximum temperature at 1.0 degree resolution"
    ),
    "tmin_1.0" = list(
      nlat = 31,
      nlon = 31,
      lat_start = 7.5,
      lat_end = 37.5,
      lon_start = 67.5,
      lon_end = 97.5,
      resolution = 1.0,
      unit = "Celsius",
      missing_value = 99.9,
      format = "Binary",
      description = "Daily minimum temperature at 1.0 degree resolution"
    )
  )

  if (!dataset %in% names(specs)) {
    stop(
      "Invalid dataset. The dataset must be one of: ",
      paste(names(specs), collapse = ", ")
    )
  }

  return(specs[[dataset]])
}

#' List available IMD datasets
#'
#' @return data.frame with the available IMD datasets and their properties.
#' @export
#' @examples
#' list_imd_datasets()
list_imd_datasets <- function() {
  datasets <- data.frame(
    dataset_id = c("rainfall_0.25", "rainfall_1.0", "tmax_1.0", "tmin_1.0"),
    variable = c("Rainfall", "Rainfall", "Max Temperature", "Min Temperature"),
    resolution = c(0.25, 1.0, 1.0, 1.0),
    year_start = c(.IMD_RAIN_YEARS[1], .IMD_RAIN_YEARS[1], .IMD_TEMP_YEARS[1], .IMD_TEMP_YEARS[1]),
    year_end = c(.IMD_RAIN_YEARS[2], .IMD_RAIN_YEARS[2], .IMD_TEMP_YEARS[2], .IMD_TEMP_YEARS[2]),
    unit = c("mm", "mm", "\u00b0C", "\u00b0C"),
    format = c("NetCDF", "NetCDF", "Binary", "Binary"),
    grid_size = c("135x129", "35x33", "31x31", "31x31"),
    missing_value = c(-999, -999, 99.9, 99.9),
    stringsAsFactors = FALSE
  )

  return(datasets)
}
