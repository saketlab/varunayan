#' Utility functions for the Varunayan R package
#'
#' @name varunayan-utils
#' @noRd
#' @importFrom stats aggregate as.formula complete.cases setNames
#' @importFrom utils setTxtProgressBar txtProgressBar write.csv
#' @importFrom graphics grid
NULL

# Stop R CMD check NOTEs for dplyr NSE variables
utils::globalVariables(c(
  ".", "..value_col", "datetime", "latitude", "longitude",
  "time_group", "time_idx", "value", "variable",
  "s", "mx", "mn", "avg", "method",
  "year", "month", "tmax", "tmin", "wbgt", "dtr", "has_data", "hot", "trop", "tx90", "tn90",
  "tx90p", "tn90p", "wsdi", "hw_day", "hw_event", "hw_len", "hw_severe", "wn_day",
  "wn_event", "wn_len", "wn_severe", "wbgt_high", "wbgt_extreme", "heat_index",
  "hi_danger", "wet_bulb", "tw31", "terrain", "i.terrain"
))

# Package environment for timing data
.varunayan_env <- new.env(parent = emptyenv())
.varunayan_env$timings <- list()

#' Find if data is valid GeoJSON
#' @param data List or data structure to examine
#' @return Logical. TRUE if the data is valid GeoJSON
is_valid_geojson <- function(data) {
  is.list(data) && "type" %in% names(data) &&
    data$type %in% c(
      "Feature", "FeatureCollection", "Polygon", "MultiPolygon",
      "Point", "MultiPoint", "LineString", "MultiLineString", "GeometryCollection"
    )
}

#' Convert data to GeoJSON format
#' @param data Data to convert (must be data.frame with lon/lat columns)
#' @return Data in GeoJSON format
convert_to_geojson <- function(data) {
  if (!is.data.frame(data) || !all(c("lon", "lat") %in% names(data))) {
    stop("Cannot convert data to GeoJSON format")
  }
  features <- lapply(seq_len(length.out = nrow(x = data)), function(i) {
    list(
      type = "Feature",
      geometry = list(type = "Point", coordinates = c(data$lon[i], data$lat[i])),
      properties = as.list(data[i, !names(data) %in% c("lon", "lat"), drop = FALSE])
    )
  })
  list(type = "FeatureCollection", features = features)
}

#' Create GeoJSON from bounding box coordinates
#' @param north Northern latitude
#' @param south Southern latitude
#' @param east Eastern longitude
#' @param west Western longitude
#' @return GeoJSON object that shows the bounding box
create_geojson_from_bbox <- function(north, south, east, west) {
  list(
    type = "Feature",
    geometry = list(
      type = "Polygon",
      coordinates = list(list(c(west, south), c(east, south), c(east, north), c(west, north), c(west, south)))
    ),
    properties = list()
  )
}

#' Create temporary GeoJSON file
#' @param geojson_data GeoJSON data to write
#' @param request_id Request identifier for a unique filename
#' @return Path to temporary GeoJSON file
create_temp_geojson_file <- function(geojson_data, request_id) {
  temp_file <- file.path(tempdir(), sprintf(fmt = "varunayan_%s_%s.geojson", request_id, format(Sys.time(), "%Y%m%d_%H%M%S")))
  write_json(geojson_data, temp_file, pretty = TRUE, auto_unbox = TRUE)
  temp_file
}

#' Parse a date string in different formats
#' @param date_string Character string in one of different date formats
#' @return Date object
parse_date_flexible <- function(date_string) {
  date <- as.Date(x = date_string, format = "%Y-%m-%d")
  if (is.na(date)) date <- suppressWarnings(ymd(date_string))
  if (is.na(date)) stop("Date '", date_string, "' must be in YYYY-MM-DD format")
  date
}

#' Get bounding box from sf object
#' @param sf_obj sf object
#' @return Named numeric vector with xmin, ymin, xmax, ymax
get_bbox_from_sf <- function(sf_obj) {
  bbox <- st_bbox(sf_obj)
  c(
    xmin = as.numeric(x = bbox["xmin"]), ymin = as.numeric(x = bbox["ymin"]),
    xmax = as.numeric(x = bbox["xmax"]), ymax = as.numeric(x = bbox["ymax"])
  )
}

#' Make sure that geographic coordinates are valid
#' @param lat Latitude value
#' @param lon Longitude value
#' @return Logical. TRUE if the coordinates are valid
validate_coordinates <- function(lat, lon) {
  !is.na(lat) && !is.na(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180
}

#' Make sure that bounding box coordinates are valid
#' @param north Northern boundary
#' @param south Southern boundary
#' @param east Eastern boundary
#' @param west Western boundary
#' @return Logical. TRUE if the bounding box is valid
validate_bbox <- function(north, south, east, west) {
  validate_coordinates(north, east) && validate_coordinates(south, west) &&
    north > south && east > west
}

#' Convert pressure levels to the character format necessary for the CDS API
#' @param pressure_levels Numeric or character vector of pressure levels
#' @return Character vector of pressure levels
format_pressure_levels <- function(pressure_levels) {
  if (is.null(pressure_levels)) {
    return(NULL)
  }

  pressure_char <- as.character(x = pressure_levels)
  valid_levels <- get_available_pressure_levels()
  invalid <- pressure_char[!pressure_char %in% valid_levels]

  if (length(x = invalid) > 0) {
    warning("Invalid pressure levels: ", paste(invalid, collapse = ", "), call. = FALSE)
  }
  pressure_char
}

#' Format date range for CDS API requests
#' @param start_date Start date (Date object)
#' @param end_date End date (Date object)
#' @return Character vector of date strings in YYYY-MM-DD format
format_date_range <- function(start_date, end_date) {
  format(seq(from = start_date, to = end_date, by = "day"), "%Y-%m-%d")
}

#' Get time values for a frequency
#' @param frequency Character string that gives the temporal frequency
#' @return Character vector of time strings
get_time_values <- function(frequency) {
  switch(frequency,
    "hourly" = sprintf(fmt = "%02d:00", 0:23),
    "daily" = "12:00",
    "monthly" = "12:00",
    sprintf(fmt = "%02d:00", 0:23)
  )
}

#' Create the output directory if it does not exist
#' @param output_dir Path to output directory
#' @return Character string. The path to the directory that the function made or found
ensure_output_dir <- function(output_dir) {
  if (!dir.exists(output_dir)) {
    dir.create(output_dir, recursive = TRUE)
    message("Created output directory: ", output_dir)
  }
  output_dir
}

#' Delete temporary files that match a pattern
#' @param pattern Regular expression pattern to match files
#' @param directory Directory for the search (default: tempdir())
#' @return Number of files removed
cleanup_temp_files <- function(pattern = "varunayan_.*", directory = tempdir()) {
  temp_files <- list.files(directory, pattern = pattern, full.names = TRUE)
  if (length(x = temp_files) > 0) {
    unlink(temp_files)
    message("Deleted ", length(x = temp_files), " temporary files")
  }
  length(x = temp_files)
}

#' Get package version information
#' @param ... Arguments for the main function (for use by aliases).
#' @return The [utils::sessionInfo()] object, invisibly. Called for its side effect of reporting the R version, platform and versions of key dependencies as messages.
#' @export
#' @examples
#' get_package_info()
get_package_info <- function() {
  pkg_info <- sessionInfo()
  message("varunayan Package Information")
  message("R version: ", pkg_info$R.version$version.string)
  message("Platform: ", pkg_info$platform)

  key_packages <- c("ecmwfr", "sf", "stars", "ncdf4", "ncmeta")
  for (pkg in key_packages) {
    if (requireNamespace(pkg, quietly = TRUE)) {
      message(pkg, ": ", packageVersion(pkg))
    } else {
      message(pkg, ": NOT INSTALLED")
    }
  }
  invisible(pkg_info)
}

#' Make sure that the system is ready for varunayan operations
#'
#' @param verbose If TRUE, print detailed information
#' @param ... Arguments for the main function (for use by aliases).
#' @return Invisibly, `TRUE` if all required packages, network access and CDS credentials are available, `FALSE` otherwise.
#' @export
#' @examplesIf interactive()
#' check_system_readiness()
check_system_readiness <- function(verbose = TRUE) {
  if (verbose) message("The system check starts...")

  issues <- character()

  for (pkg in c("ecmwfr", "sf", "stars", "ncdf4", "ncmeta")) {
    if (!requireNamespace(pkg, quietly = TRUE)) {
      issues <- c(issues, paste("Package", pkg, "is not available"))
    } else if (verbose) {
      message(pkg, ": OK")
    }
  }

  network_ok <- tryCatch(
    {
      con <- url("https://httpbin.org/status/200", open = "rb")
      close(con)
      TRUE
    },
    error = function(e) FALSE
  )

  if (!network_ok) {
    issues <- c(issues, "Network connection problem")
  } else if (verbose) {
    message("Network: OK")
  }

  # Examine the CDS credentials
  if (!get_cds_credentials(silent = !verbose)) {
    issues <- c(issues, "CDS API credentials are not configured")
  }

  if (length(x = issues) == 0) {
    if (verbose) message("The system is ready")
    return(invisible(TRUE))
  } else {
    if (verbose) {
      warning("The check found these problems:", call. = FALSE)
      for (issue in issues) message("  - ", issue)
    }
    return(invisible(FALSE))
  }
}


#' Measure the time of an operation and record the duration
#'
#' @param expr Expression to measure
#' @param label Label for the operation
#' @param verbose If TRUE, print the time information (default: TRUE)
#' @return The value of `expr`. The elapsed time is recorded and can be retrieved with [get_timings()].
#' @export
#' @examples
#' x <- time_operation(sum(1:10), "sum")
#' get_timings()
time_operation <- function(expr, label, verbose = TRUE) {
  start <- Sys.time()
  if (verbose) message("[TIMER] Start: ", label)

  result <- force(expr)

  elapsed <- as.numeric(x = difftime(Sys.time(), start, units = "secs"))
  if (verbose) {
    time_str <- if (elapsed < 1) {
      paste0(round(elapsed * 1000, 1), " ms")
    } else if (elapsed < 60) {
      paste0(round(elapsed, 2), " sec")
    } else {
      paste0(floor(elapsed / 60), "m ", round(elapsed %% 60, 1), "s")
    }
    message("[TIMER] ", label, ": ", time_str)
  }

  .varunayan_env$timings[[length(x = .varunayan_env$timings) + 1]] <- list(
    label = label, elapsed = elapsed, timestamp = Sys.time()
  )
  result
}

#' Get all recorded time measurements
#' @return A data.frame with columns `label`, `elapsed_seconds`, `timestamp` and `duration` (formatted), one row per timed operation; zero rows if nothing has been timed.
#' @export
#' @examples
#' get_timings()
get_timings <- function() {
  timings <- .varunayan_env$timings
  if (length(x = timings) == 0) {
    message("There is no recorded time data")
    return(data.frame(label = character(), elapsed_seconds = numeric(), timestamp = character()))
  }

  df <- data.frame(
    label = sapply(timings, `[[`, "label"),
    elapsed_seconds = sapply(timings, `[[`, "elapsed"),
    timestamp = sapply(timings, function(x) format(x$timestamp, "%Y-%m-%d %H:%M:%S")),
    stringsAsFactors = FALSE
  )
  df$duration <- sapply(df$elapsed_seconds, function(s) {
    if (s < 1) {
      sprintf(fmt = "%.1f ms", s * 1000)
    } else if (s < 60) {
      sprintf(fmt = "%.2f sec", s)
    } else {
      sprintf(fmt = "%dm %.1fs", floor(s / 60), s %% 60)
    }
  })
  df
}

#' Clear all time data
#' @return `NULL`, invisibly. Called for its side effect.
#' @export
#' @examples
#' clear_timings()
clear_timings <- function() {
  .varunayan_env$timings <- list()
  message("The function cleared the time data")
}

#' Print a summary of the time data
#' @return The timing data frame from [get_timings()], invisibly (`NULL` if empty).
#' @export
#' @examples
#' print_timing_summary()
print_timing_summary <- function() {
  df <- get_timings()
  if (nrow(x = df) == 0) {
    message("No time data to show")
    return(invisible(NULL))
  }

  message("\n=== Performance Time Summary ===\n")
  message("Total operations: ", nrow(x = df))
  message("Total time: ", round(sum(df$elapsed_seconds), 2), " seconds\n")

  df <- df[order(-df$elapsed_seconds), ]
  message("Operations (slowest first):")
  for (i in seq_len(length.out = nrow(x = df))) {
    pct <- round(100 * df$elapsed_seconds[i] / sum(df$elapsed_seconds), 1)
    message(i, ". ", df$label[i], ": ", df$duration[i], " (", pct, "%)")
  }
  invisible(df)
}


#' Read CDS API credentials from ~/.cdsapirc file
#' @param file_path Path to .cdsapirc file (default: "~/.cdsapirc")
#' @return A named list of the fields in the file (typically `url` and `key`), or `NULL` if the file does not exist or cannot be parsed.
#' @export
#' @examples
#' f <- tempfile()
#' writeLines(c("url: https://cds.climate.copernicus.eu/api", "key: abc-123"), f)
#' read_cdsapirc(f)
read_cdsapirc <- function(file_path = "~/.cdsapirc") {
  file_path <- path.expand(file_path)
  if (!file.exists(file_path)) {
    return(NULL)
  }

  tryCatch(
    {
      lines <- readLines(file_path, warn = FALSE)
      creds <- list()
      for (line in lines) {
        line <- trimws(x = line)
        if (nchar(line) == 0 || grepl(pattern = "^#", line)) next
        if (grepl(pattern = ":", line)) {
          parts <- strsplit(x = line, split = ":", fixed = TRUE)[[1]]
          if (length(x = parts) >= 2) {
            creds[[trimws(x = parts[1])]] <- trimws(x = paste(parts[-1], collapse = ":"))
          }
        }
      }
      if ("key" %in% names(creds)) creds else NULL
    },
    error = function(e) NULL
  )
}

#' Get CDS API credentials from different sources
#'
#' Checks the `CDS_API_KEY` environment variable, then the 'ecmwfr' keyring,
#' then `~/.cdsapirc`. A key found in the environment variable or in
#' `~/.cdsapirc` is registered with 'ecmwfr' via [ecmwfr::wf_set_key()].
#'
#' @param silent If TRUE, do not show information messages
#' @return `TRUE` if credentials are available, `FALSE` otherwise.
#' @export
#' @examplesIf interactive()
#' get_cds_credentials()
get_cds_credentials <- function(silent = FALSE) {
  register <- function(key, source) {
    if (!silent) message("Load CDS credentials from ", source, "...")
    tryCatch(
      {
        suppressWarnings(wf_set_key(key = key))
        if (!silent) message("CDS credentials are configured")
        TRUE
      },
      error = function(e) FALSE
    )
  }

  # env var first so parallel workers can use different keys
  env_key <- Sys.getenv("CDS_API_KEY", unset = "")
  if (nzchar(env_key) && register(env_key, "the CDS_API_KEY environment variable")) {
    return(TRUE)
  }

  has_creds <- suppressWarnings(tryCatch(
    {
      key <- wf_get_key()
      !is.null(key) && nchar(key) > 0
    },
    error = function(e) FALSE
  ))

  if (has_creds) {
    if (!silent) message("The package found the CDS credentials")
    return(TRUE)
  }

  creds <- read_cdsapirc()
  if (!is.null(creds) && "key" %in% names(creds) && register(creds$key, "~/.cdsapirc")) {
    return(TRUE)
  }

  if (!silent) {
    warning("Cannot find CDS credentials", call. = FALSE)
    message("Run setup_cds_credentials(key = 'your-api-key')")
  }
  FALSE
}


#' Switch off spherical geometry (s2) until the calling function returns
#'
#' With s2 off, sf uses planar coordinates. For grid cells and Indian polygons,
#' this is sufficient and faster. sf writes a message at each change of s2,
#' thus this function does not show these messages.
#' @noRd
local_s2_off <- function(envir = parent.frame()) {
  old <- sf::sf_use_s2()
  suppressMessages(sf::sf_use_s2(FALSE))
  do.call(on.exit, list(bquote(suppressMessages(sf::sf_use_s2(.(old)))), add = TRUE), envir = envir)
  invisible(old)
}
