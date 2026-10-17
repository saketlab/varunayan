.CDS_KEY_URL <- "https://cds.climate.copernicus.eu/how-to-api"

.require_cds_credentials <- function() {
  if (!get_cds_credentials(silent = TRUE)) {
    stop(
      "Cannot find the CDS credentials. Do one of these steps:\n",
      "  1. Create the ~/.cdsapirc file with your API key, or\n",
      "  2. Run setup_cds_credentials(key = 'your-api-key')\n\n",
      "Get your API key from: ", .CDS_KEY_URL,
      call. = FALSE
    )
  }
}

.stop_cds_auth_failed <- function() {
  stop(
    "Authentication failed. Examine your CDS API credentials.\n",
    "Run setup_cds_credentials(key = 'your-api-key') with a correct key.\n",
    "Get your API key from: ", .CDS_KEY_URL,
    call. = FALSE
  )
}

# ERA5 data download functions that use ecmwfr

# If the error is related to size, signal the cds_request_too_large condition.
# The function treats "Request has failed" as size-related only for ranges > 400 days.
signal_if_too_large <- function(err_msg, start_date, end_date) {
  is_size <- grepl("cost limits|too large|request is too large", err_msg, ignore.case = TRUE)
  range_days <- as.numeric(as.Date(end_date) - as.Date(start_date))
  is_generic <- grepl("Request has failed", err_msg) && range_days > 400
  if (is_size || is_generic) {
    cond <- simpleCondition(
      message = paste0("The CDS request is too large: ", err_msg),
      call = sys.call(-2)
    )
    class(cond) <- c("cds_request_too_large", "error", "condition")
    stop(cond)
  }
}

# Variables that the monthly-means product does not supply (they must use hourly reanalysis)
.MONTHLY_MEANS_UNSUPPORTED <- c(
  "maximum_2m_temperature_since_previous_post_processing",
  "minimum_2m_temperature_since_previous_post_processing"
)

#' Configure CDS credentials for ERA5 data access
#'
#' This function configures the Copernicus Climate Data Store (CDS) credentials
#' for ERA5 downloads. The function examines the credentials in this order:
#' 1. The `key` argument that you give directly
#' 2. `CDS_API_KEY` environment variable
#' 3. `~/.cdsapirc` file
#'
#' @param key Your CDS API key (UUID format). If NULL, the function tries to read
#'   the key from the `CDS_API_KEY` environment variable or the ~/.cdsapirc file.
#' @param ... Arguments passed to the main function (used by aliases).
#' @return Invisibly, `TRUE` once the key has been registered with 'ecmwfr'. Errors if no key can be found.
#' @export
#' @examples
#' \dontrun{
#' setup_cds_credentials(key = "your-cds-api-key-here")
#' Sys.setenv(CDS_API_KEY = "your-cds-api-key-here")
#' setup_cds_credentials()
#' }
setup_cds_credentials <- function(key = NULL) {
  if (is.null(key)) {
    env_key <- Sys.getenv("CDS_API_KEY", unset = "")
    if (nzchar(env_key)) {
      key <- env_key
      message("The package uses the CDS API key from the CDS_API_KEY environment variable")
    } else {
      message("You did not give a key. The package tries to read the key from ~/.cdsapirc...")
      creds <- read_cdsapirc()

      if (is.null(creds) || !"key" %in% names(creds)) {
        stop(
          "Cannot find the CDS credentials.\n",
          "Give the credentials with one of these methods:\n",
          "  1. Give the key directly: setup_cds_credentials(key = 'your-api-key')\n",
          "  2. Set the environment variable: Sys.setenv(CDS_API_KEY = 'your-api-key')\n",
          "  3. Create the ~/.cdsapirc file with this format:\n",
          "     url: https://cds.climate.copernicus.eu/api\n",
          "     key: your-api-key-here\n\n",
          "Get your API key from: ", .CDS_KEY_URL
        )
      }

      key <- creds$key
      message("The package found the credentials in ~/.cdsapirc")
    }
  }

  suppressWarnings({
    wf_set_key(key = key)
  })

  message("The CDS credentials are set.")
  message("You can now download ERA5 data with the varunayan functions.")

  invisible(TRUE)
}


#' Download ERA5 single-level data with ecmwfr
#'
#' @param variables Character vector of variable names
#' @param start_date Date object or character string (YYYY-MM-DD)
#' @param end_date Date object or character string (YYYY-MM-DD)
#' @param area Numeric vector of 4 elements: c(north, west, south, east) in decimal degrees
#' @param resolution Numeric value for grid resolution (default: 0.25 degrees)
#' @param frequency Character string: "hourly", "daily", "monthly"
#' @param output_file Character string path for output NetCDF file
#' @param timeout Numeric value for request timeout in seconds (default: 3600)
#' @param retry_attempts Integer number of retry attempts (default: 5)
#' @param use_cache If TRUE, use cached data when it is available (default: TRUE)
#' @param verbose Logical. If TRUE, print progress messages
#' @return Character string path to downloaded file
download_era5_single <- function(variables, start_date, end_date, area = NULL,
                                 resolution = 0.25, frequency = "hourly", output_file,
                                 timeout = 3600, retry_attempts = 5, use_cache = TRUE,
                                 verbose = FALSE) {
  # The monthly-means product is faster. It does not use per-day chunks.
  use_monthly_means <- (frequency == "monthly") &&
    !any(variables %in% .MONTHLY_MEANS_UNSUPPORTED)

  if (use_cache) {
    cache_key <- generate_cache_key(
      source = "era5",
      variables = variables,
      start_date = start_date,
      end_date = end_date,
      area = area,
      resolution = resolution,
      dataset_type = if (use_monthly_means) "single_monthly_means" else "single"
    )

    cached_file <- check_cache(cache_key)
    if (!is.null(cached_file)) {
      message(sprintf(fmt = "The package uses cached data: %s", basename(path = cached_file)))
      message(sprintf(fmt = "Cache location: %s", cached_file))
      file.copy(cached_file, output_file, overwrite = TRUE)
      return(output_file)
    }
  }

  start_str <- format(as.Date(x = start_date), "%Y-%m-%d")
  end_str <- format(as.Date(x = end_date), "%Y-%m-%d")

  if (use_monthly_means) {
    month_seq <- seq(from = as.Date(x = start_date), to = as.Date(x = end_date), by = "month")
    years <- as.list(unique(format(month_seq, "%Y")))
    months <- as.list(unique(format(month_seq, "%m")))

    request <- list(
      product_type = list("monthly_averaged_reanalysis"),
      data_format = "netcdf",
      download_format = "unarchived",
      variable = as.list(variables),
      year = years,
      month = months,
      time = list("00:00")
    )
  } else {
    date_seq <- seq(from = as.Date(x = start_date), to = as.Date(x = end_date), by = "day")
    date_strings <- format(date_seq, "%Y-%m-%d")

    time_values <- switch(frequency,
      "hourly" = sprintf(fmt = "%02d:00", 0:23),
      "daily" = "12:00",
      sprintf(fmt = "%02d:00", 0:23)
    )

    request <- list(
      product_type = list("reanalysis"),
      data_format = "netcdf",
      download_format = "unarchived",
      variable = as.list(variables),
      date = as.list(date_strings),
      time = as.list(time_values)
    )
  }

  if (!is.null(area)) {
    request$area <- area
  }

  request$dataset_short_name <- if (use_monthly_means) {
    "reanalysis-era5-single-levels-monthly-means"
  } else {
    "reanalysis-era5-single-levels"
  }
  request$target <- basename(path = output_file)

  .require_cds_credentials()

  message("The package sends the request to Copernicus CDS...")
  message(sprintf(fmt = "Variables: %s", paste(variables, collapse = ", ")))
  message(sprintf(fmt = "Date range: %s to %s", start_str, end_str))
  if (!is.null(area)) {
    message(sprintf(fmt = "Area: N:%s, W:%s, S:%s, E:%s", area[1], area[2], area[3], area[4]))
  }

  message("Note: An ERA5 download can take several minutes. The time changes with the data size and the server load.")
  message(sprintf(fmt = "The request will stop after a timeout of %s seconds", timeout))

  downloaded_file <- NULL
  last_error <- NULL
  failures <- 0
  rate_limit_hits <- 0
  max_rate_limit_hits <- 20
  effective_retries <- if (use_monthly_means) 1L else retry_attempts

  repeat {
    if (failures > 0) {
      message(sprintf(fmt = "Retry attempt %s/%s", failures, retry_attempts))
      Sys.sleep(5)
    }

    downloaded_file <- tryCatch(
      {
        if (requireNamespace("R.utils", quietly = TRUE)) {
          R.utils::withTimeout(
            wf_request(
              request = request,
              transfer = TRUE,
              path = dirname(path = output_file)
            ),
            timeout = timeout,
            onTimeout = "error"
          )
        } else {
          wf_request(
            request = request,
            transfer = TRUE,
            path = dirname(path = output_file)
          )
        }
      },
      error = function(e) e
    )
    if (inherits(downloaded_file, "error")) {
      last_error <- downloaded_file
      downloaded_file <- NULL
    }

    if (!is.null(downloaded_file)) break

    if (!is.null(last_error)) {
      if (grepl(pattern = "401|unauthorized|authentication", last_error$message, ignore.case = TRUE)) {
        .stop_cds_auth_failed()
      } else if (grepl(pattern = "rate.limit|429", last_error$message, ignore.case = TRUE)) {
        rate_limit_hits <- rate_limit_hits + 1
        if (rate_limit_hits > max_rate_limit_hits) {
          stop("The number of rate-limit retries is more than ", max_rate_limit_hits, ". Try again later.")
        }
        wait_secs <- as.numeric(sub(".*wait (\\d+) seconds.*", "\\1", last_error$message))
        if (is.na(wait_secs)) wait_secs <- 60
        warning(sprintf(
          fmt = "CDS applied the rate limit (%d/%d). The package waits %s seconds...",
          rate_limit_hits, max_rate_limit_hits, wait_secs
        ), call. = FALSE)
        Sys.sleep(wait_secs)
        next # skip the 5s sleep at the top because we waited already
      } else if (grepl(pattern = "timeout|time.*out", last_error$message, ignore.case = TRUE)) {
        failures <- failures + 1
        warning(sprintf(fmt = "Timeout on attempt %s. The package tries again...", failures), call. = FALSE)
      } else if (grepl(pattern = "queue|busy|server", last_error$message, ignore.case = TRUE)) {
        failures <- failures + 1
        warning(sprintf(fmt = "The CDS server is busy on attempt %s. The package tries again...", failures), call. = FALSE)
      } else {
        failures <- failures + 1
        warning(sprintf(fmt = "Download failed on attempt %s: %s", failures, last_error$message), call. = FALSE)
      }
    } else {
      failures <- failures + 1
    }

    if (failures > effective_retries) {
      if (use_monthly_means && !is.null(last_error)) {
        message("The monthly-means request failed. The package uses the regular reanalysis dataset...")
        use_monthly_means <- FALSE

        date_seq <- seq(from = as.Date(x = start_date), to = as.Date(x = end_date), by = "day")
        request$product_type <- list("reanalysis")
        request$date <- as.list(format(date_seq, "%Y-%m-%d"))
        request$time <- list("12:00")
        request$year <- NULL
        request$month <- NULL
        request$dataset_short_name <- "reanalysis-era5-single-levels"

        failures <- 0
        last_error <- NULL
        effective_retries <- retry_attempts
        next
      }
      err_msg <- if (!is.null(last_error)) last_error$message else "unknown error"

      signal_if_too_large(err_msg, start_date, end_date)

      stop(
        sprintf("Download failed after %d attempts: ", failures),
        err_msg, "\n",
        "Examine your internet connection and the CDS service status at: https://cds.climate.copernicus.eu/"
      )
    }
  }

  if (!is.null(downloaded_file) && file.exists(downloaded_file)) {
    final_file <- downloaded_file
    if (file_ext(downloaded_file) == "zip") {
      final_file <- extract_zip_to_nc(downloaded_file, dirname(path = output_file))
    }
  } else {
    final_file <- find_and_extract_download(output_file, request$target)
  }

  message(sprintf(fmt = "Download completed: %s", final_file))

  if (use_cache) {
    tryCatch(
      save_to_cache(final_file, cache_key),
      error = function(e) warning(sprintf(fmt = "Cannot save to the cache: %s", e$message), call. = FALSE)
    )
  }

  final_file
}

#' Download ERA5 pressure-level data with ecmwfr
#'
#' @param variables Character vector of variable names
#' @param pressure_levels Character vector of pressure levels (e.g., c("1000", "850", "500"))
#' @param start_date Date object or character string (YYYY-MM-DD)
#' @param end_date Date object or character string (YYYY-MM-DD)
#' @param area Numeric vector of 4 elements: c(north, west, south, east) in decimal degrees
#' @param resolution Numeric value for grid resolution (default: 0.25 degrees)
#' @param frequency Character string: "hourly", "daily", "monthly"
#' @param output_file Character string path for output NetCDF file
#' @param use_cache If TRUE, use cached data when it is available (default: TRUE)
#' @param verbose Logical. If TRUE, print progress messages
#' @return Character string path to downloaded file
download_era5_pressure <- function(variables, pressure_levels, start_date, end_date,
                                   area = NULL, resolution = 0.25, frequency = "hourly",
                                   output_file, use_cache = TRUE, verbose = FALSE) {
  if (use_cache) {
    cache_key <- generate_cache_key(
      source = "era5",
      variables = variables,
      start_date = start_date,
      end_date = end_date,
      area = area,
      resolution = resolution,
      dataset_type = "pressure",
      pressure_levels = pressure_levels
    )

    cached_file <- check_cache(cache_key)
    if (!is.null(cached_file)) {
      message(sprintf(fmt = "The package uses cached data: %s", basename(path = cached_file)))
      message(sprintf(fmt = "Cache location: %s", cached_file))
      file.copy(cached_file, output_file, overwrite = TRUE)
      return(output_file)
    }
  }

  start_str <- format(as.Date(x = start_date), "%Y-%m-%d")
  end_str <- format(as.Date(x = end_date), "%Y-%m-%d")

  date_seq <- seq(from = as.Date(x = start_date), to = as.Date(x = end_date), by = "day")
  date_strings <- format(date_seq, "%Y-%m-%d")

  time_values <- switch(frequency,
    "hourly" = sprintf(fmt = "%02d:00", 0:23),
    "daily" = "12:00",
    "monthly" = "12:00",
    sprintf(fmt = "%02d:00", 0:23)
  )

  request <- list(
    product_type = list("reanalysis"),
    data_format = "netcdf",
    download_format = "unarchived",
    variable = as.list(variables),
    pressure_level = as.list(pressure_levels),
    date = as.list(date_strings),
    time = as.list(time_values)
  )

  if (!is.null(area)) {
    request$area <- area
  }

  request$dataset_short_name <- "reanalysis-era5-pressure-levels"
  request$target <- basename(path = output_file)

  .require_cds_credentials()

  message("The package sends the pressure-level request to Copernicus CDS...")
  message(sprintf(fmt = "Variables: %s", paste(variables, collapse = ", ")))
  message(sprintf(fmt = "Pressure levels: %s hPa", paste(pressure_levels, collapse = ", ")))
  message(sprintf(fmt = "Date range: %s to %s", start_str, end_str))
  if (!is.null(area)) {
    message(sprintf(fmt = "Area: N:%s, W:%s, S:%s, E:%s", area[1], area[2], area[3], area[4]))
  }

  message("Note: An ERA5 download can take several minutes. The time changes with the data size and the server load.")

  downloaded_file <- tryCatch(
    {
      wf_request(
        request = request,
        transfer = TRUE,
        path = dirname(path = output_file)
      )
    },
    error = function(e) {
      if (grepl(pattern = "401|unauthorized|authentication", e$message, ignore.case = TRUE)) {
        .stop_cds_auth_failed()
      }

      signal_if_too_large(e$message, start_date, end_date)

      if (grepl(pattern = "timeout|time.*out", e$message, ignore.case = TRUE)) {
        stop(
          "Timeout of the request. This can occur with large data requests.\n",
          "Decrease the date range or the area size. Or, try again later.\n",
          "For large datasets, use smaller time chunks or a lower resolution."
        )
      } else if (grepl(pattern = "queue|busy|server", e$message, ignore.case = TRUE)) {
        stop(
          "The CDS server is busy. Try again later.\n",
          "At peak times, the wait can be longer, or a timeout can occur."
        )
      } else {
        stop(
          "Download failed: ", e$message, "\n",
          "Examine your internet connection and the CDS service status at: https://cds.climate.copernicus.eu/"
        )
      }
    }
  )

  if (!is.null(downloaded_file) && file.exists(downloaded_file)) {
    final_file <- downloaded_file
    if (file_ext(downloaded_file) == "zip") {
      final_file <- extract_zip_to_nc(downloaded_file, dirname(path = output_file))
    }
  } else {
    final_file <- find_and_extract_download(output_file, request$target)
  }

  message(sprintf(fmt = "Pressure-level download completed: %s", final_file))

  if (use_cache) {
    tryCatch(
      save_to_cache(final_file, cache_key),
      error = function(e) warning(sprintf(fmt = "Cannot save to the cache: %s", e$message), call. = FALSE)
    )
  }

  final_file
}

extract_zip_to_nc <- function(zip_file, output_dir) {
  message(sprintf(fmt = "The package extracts the ZIP file: %s", basename(path = zip_file)))

  temp_extract_dir <- file.path(output_dir, "extracted")
  dir.create(temp_extract_dir, showWarnings = FALSE)
  on.exit(unlink(temp_extract_dir, recursive = TRUE), add = TRUE)

  unzip(zip_file, exdir = temp_extract_dir)

  nc_files <- list.files(temp_extract_dir, pattern = "\\.nc$", full.names = TRUE)

  if (length(x = nc_files) == 0) {
    stop("The ZIP archive does not contain NetCDF files: ", zip_file)
  }

  if (length(x = nc_files) > 1) {
    message(sprintf(fmt = "The package merges %d NetCDF files from the ZIP file", length(x = nc_files)))
    final_file <- merge_nc_files(nc_files, output_dir)
  } else {
    final_file <- file.path(output_dir, basename(path = nc_files[1]))
    file.copy(nc_files[1], final_file, overwrite = TRUE)
  }

  unlink(zip_file)

  final_file
}

merge_nc_files <- function(nc_files, output_dir) {
  all_vars <- list()
  shared_dims <- NULL

  for (f in nc_files) {
    nc <- ncdf4::nc_open(f)
    tryCatch({
      dim_names <- names(nc$dim)
      climate_vars <- setdiff(names(nc$var), .NC_METADATA_VARS)

      for (vname in climate_vars) {
        vdata <- ncdf4::ncvar_get(nc, vname)
        vunits <- tryCatch(ncdf4::ncatt_get(nc, vname, "units")$value, error = function(e) "")
        all_vars[[vname]] <- list(data = vdata, units = vunits, dims = nc$var[[vname]]$dim)
      }

      if (is.null(shared_dims)) {
        shared_dims <- list()
        for (dname in dim_names) {
          d <- nc$dim[[dname]]
          shared_dims[[dname]] <- list(vals = d$vals, units = d$units, unlim = d$unlim)
        }
      }
    }, finally = {
      ncdf4::nc_close(nc)
    })
  }

  if (length(all_vars) == 0) stop("The NetCDF files do not contain climate variables")

  merged_file <- file.path(output_dir, paste0("merged_", basename(nc_files[1])))

  nc_dims <- list()
  for (dname in names(shared_dims)) {
    d <- shared_dims[[dname]]
    nc_dims[[dname]] <- ncdf4::ncdim_def(dname, d$units, d$vals, unlim = d$unlim)
  }

  nc_var_defs <- list()
  for (vname in names(all_vars)) {
    v <- all_vars[[vname]]
    var_dims <- list()
    for (vd in v$dims) {
      if (vd$name %in% names(nc_dims)) {
        var_dims <- c(var_dims, list(nc_dims[[vd$name]]))
      }
    }
    nc_var_defs[[vname]] <- ncdf4::ncvar_def(vname, v$units, var_dims, missval = NA)
  }

  nc_out <- ncdf4::nc_create(merged_file, nc_var_defs)
  tryCatch({
    for (vname in names(all_vars)) {
      ncdf4::ncvar_put(nc_out, vname, all_vars[[vname]]$data)
    }
  }, error = function(e) {
    unlink(merged_file)
    stop(e)
  }, finally = {
    ncdf4::nc_close(nc_out)
  })

  message(sprintf(fmt = "Merged %d variables into: %s", length(all_vars), basename(merged_file)))
  merged_file
}

find_and_extract_download <- function(output_file, target) {
  base_name <- file_path_sans_ext(basename(path = output_file))
  base_dir <- dirname(path = output_file)

  possible_files <- c(
    output_file,
    file.path(base_dir, paste0(base_name, ".zip")),
    file.path(base_dir, target)
  )

  actual_file <- NULL
  for (pf in possible_files) {
    if (file.exists(pf)) {
      actual_file <- pf
      break
    }
  }

  if (is.null(actual_file)) {
    stop("Cannot find the downloaded file. The package looked for these files: ", paste(possible_files, collapse = ", "))
  }

  final_file <- actual_file
  if (file_ext(actual_file) == "zip") {
    final_file <- extract_zip_to_nc(actual_file, base_dir)
  }

  final_file
}

.varunayan_cache <- new.env(parent = emptyenv())

#' Validate ERA5 variable names
#'
#' @param variables Character vector of variable names to validate
#' @param dataset_type Character string: "single" or "pressure"
#' @return Logical vector that shows which variables are valid
validate_era5_variables <- function(variables, dataset_type) {
  cache_key <- paste0("valid_vars_", dataset_type)

  if (!exists(cache_key, envir = .varunayan_cache)) {
    if (dataset_type == "single") {
      valid_vars <- get_single_level_variable_names()
    } else if (dataset_type == "pressure") {
      valid_vars <- get_pressure_level_variable_names()
    } else {
      stop("Invalid dataset_type. It must be 'single' or 'pressure'")
    }
    assign(cache_key, valid_vars, envir = .varunayan_cache)
  } else {
    valid_vars <- get(cache_key, envir = .varunayan_cache)
  }

  variables %in% valid_vars
}

#' Get all valid single-level variable names
#'
#' @return Character vector of valid single-level variable names
get_single_level_variable_names <- function() {
  c(
    "2m_temperature", "surface_pressure", "mean_sea_level_pressure",
    "total_precipitation", "convective_precipitation", "large_scale_precipitation",
    "10m_u_component_of_wind", "10m_v_component_of_wind",
    "surface_solar_radiation_downwards", "surface_thermal_radiation_downwards",
    "2m_dewpoint_temperature", "skin_temperature", "total_cloud_cover",
    "low_cloud_cover", "medium_cloud_cover", "high_cloud_cover",
    "surface_latent_heat_flux", "surface_sensible_heat_flux",
    "evaporation", "runoff", "soil_temperature_level_1",
    "soil_temperature_level_2", "soil_temperature_level_3",
    "soil_temperature_level_4", "volumetric_soil_water_layer_1",
    "volumetric_soil_water_layer_2", "volumetric_soil_water_layer_3",
    "volumetric_soil_water_layer_4", "snow_depth", "snow_density",
    "maximum_2m_temperature_since_previous_post_processing",
    "minimum_2m_temperature_since_previous_post_processing"
  )
}

#' Get all valid pressure-level variable names
#'
#' @return Character vector of valid pressure-level variable names
get_pressure_level_variable_names <- function() {
  c(
    "temperature", "u_component_of_wind", "v_component_of_wind",
    "geopotential", "relative_humidity", "specific_humidity",
    "vertical_velocity", "vorticity", "divergence"
  )
}
