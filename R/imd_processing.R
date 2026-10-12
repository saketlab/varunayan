# Rainfall variable names seen in IMD NetCDF files, current format first
.IMD_RAIN_VARS <- c("RAINFALL", "rf", "rainfall", "rain", "precip")

#' Read IMD binary temperature file
#'
#' Reads IMD binary temperature data (max or min) and converts to data.frame.
#'
#' @param file_path Path to IMD binary file (.grd).
#' @param var_type Variable type: "tmax" or "tmin".
#' @param year Year of the data.
#' @return data.frame with columns: date, latitude, longitude, temperature
#' @export
#' @examplesIf interactive()
#' f <- download_imd_temperature(2023, 2023, var_type = "tmax")
#' tmax_data <- read_imd_temperature(f, "tmax", 2023)
read_imd_temperature <- function(file_path, var_type, year) {
  if (!file.exists(file_path)) stop("File not found: ", file_path)

  dataset_id <- paste0(var_type, "_1.0")
  grid_specs <- get_imd_grid_specs(dataset_id)

  message(sprintf(fmt = "Reading IMD %s data for %s", var_type, year))
  message(sprintf(fmt = "Grid: %sx%s points", grid_specs$nlat, grid_specs$nlon))

  n_days <- if (is_leap_year(year)) 366 else 365

  con <- file(file_path, "rb")
  tryCatch({
    n_values <- n_days * grid_specs$nlat * grid_specs$nlon
    raw_data <- readBin(con, "numeric", n = n_values, size = 4, endian = "little")

    if (length(x = raw_data) != n_values) {
      warning(sprintf(fmt = "Expected %s values but got %s", n_values, length(x = raw_data)), call. = FALSE)
    }
  }, finally = {
    close(con)
  })

  dates <- seq(as.Date(x = paste0(year, "-01-01")), as.Date(x = paste0(year, "-12-31")), by = "day")

  lats <- seq(grid_specs$lat_start, grid_specs$lat_end, by = grid_specs$resolution)
  lons <- seq(grid_specs$lon_start, grid_specs$lon_end, by = grid_specs$resolution)

  if (length(x = lats) != grid_specs$nlat) {
    warning(sprintf(fmt = "Latitude grid mismatch: expected %s, got %s", grid_specs$nlat, length(x = lats)), call. = FALSE)
    lats <- lats[1:grid_specs$nlat]
  }
  if (length(x = lons) != grid_specs$nlon) {
    warning(sprintf(fmt = "Longitude grid mismatch: expected %s, got %s", grid_specs$nlon, length(x = lons)), call. = FALSE)
    lons <- lons[1:grid_specs$nlon]
  }

  data_array <- array(raw_data, dim = c(grid_specs$nlon, grid_specs$nlat, n_days))

  grid <- expand.grid(
    longitude = lons,
    latitude = lats,
    date = dates,
    KEEP.OUT.ATTRS = FALSE,
    stringsAsFactors = FALSE
  )

  grid$temperature <- as.vector(data_array)

  # Filter missing values (99.9 for temperature)
  result_df <- grid[!is.na(grid$temperature) & grid$temperature < 99, c("date", "latitude", "longitude", "temperature")]
  rownames(result_df) <- NULL

  message(sprintf(fmt = "Processed %s data points", nrow(x = result_df)))
  result_df
}

#' Read IMD NetCDF rainfall file
#'
#' Reads IMD NetCDF rainfall data and converts to data.frame.
#'
#' @param file_path Path to IMD NetCDF file (.nc).
#' @param resolution Spatial resolution: 0.25 or 1.0.
#' @param year Year of the data.
#' @param bbox Optional named list/vector (north, south, east, west). When set,
#'   only that spatial slab is read off disk (fast path); NULL reads the full grid.
#' @return data.frame with columns: date, latitude, longitude, rainfall
#' @export
#' @examplesIf interactive()
#' f <- download_imd_rainfall(2023, 2023, resolution = 0.25)
#' rain_data <- read_imd_rainfall(f, 0.25, 2023)
read_imd_rainfall <- function(file_path, resolution, year, bbox = NULL) {
  if (!file.exists(file_path)) stop("File not found: ", file_path)

  if (!is.null(bbox)) {
    return(read_imd_rainfall_cropped(file_path, year, bbox))
  }

  dataset_id <- paste0("rainfall_", format(resolution, nsmall = 1))
  grid_specs <- get_imd_grid_specs(dataset_id)

  message(sprintf(fmt = "Reading IMD rainfall data for %s", year))
  message(sprintf(fmt = "Resolution: %s\u00b0", resolution))

  rainfall_data <- tryCatch(
    read_ncdf(file_path),
    error = function(e) {
      warning(sprintf(fmt = "read_ncdf failed, trying ncdf4: %s", e$message), call. = FALSE)
      read_imd_rainfall_ncdf4(file_path, grid_specs, year)
    }
  )

  if (inherits(rainfall_data, "stars")) {
    df <- as.data.frame(rainfall_data)

    names(df) <- tolower(names(df))
    name_map <- c(
      lon = "longitude", lat = "latitude", time = "date",
      x = "longitude", y = "latitude"
    )
    for (old in names(name_map)) {
      if (old %in% names(df)) names(df)[names(df) == old] <- name_map[old]
    }

    for (col in names(df)) {
      if (inherits(df[[col]], "units")) df[[col]] <- as.numeric(df[[col]])
    }

    rain_col <- c(
      intersect(.IMD_RAIN_VARS, names(df)),
      setdiff(x = names(x = df), y = c("longitude", "latitude", "date"))
    )[1]

    if (rain_col != "rainfall") names(df)[names(df) == rain_col] <- "rainfall"
    df <- df[, c("date", "latitude", "longitude", "rainfall")]

    if (!inherits(df$date, "Date")) df$date <- as.Date(x = df$date)
    df <- df[!is.na(df$rainfall) & df$rainfall > -900, ]
  } else {
    df <- rainfall_data
  }

  message(sprintf(fmt = "Processed %s data points", nrow(x = df)))
  df
}

#' Read IMD NetCDF using ncdf4
#'
#' @param file_path Path to NetCDF file
#' @param grid_specs Grid specifications
#' @param year Year of data
#' @return data.frame
#' @keywords internal
read_imd_rainfall_ncdf4 <- function(file_path, grid_specs, year) {
  nc <- nc_open(file_path)

  tryCatch({
    dims <- names(nc$dim)
    vars <- names(nc$var)

    message(sprintf(fmt = "NetCDF dimensions: %s", paste(dims, collapse = ", ")))
    message(sprintf(fmt = "NetCDF variables: %s", paste(vars, collapse = ", ")))

    lats <- as.vector(ncvar_get(nc, "lat"))
    lons <- as.vector(ncvar_get(nc, "lon"))

    rain_var <- c(intersect(.IMD_RAIN_VARS, vars), setdiff(vars, c("lat", "lon", "time")))[1]
    if (is.na(rain_var)) stop("No rainfall variable found in NetCDF file")

    rainfall <- ncvar_get(nc, rain_var)

    n_days <- if (is_leap_year(year)) 366 else 365
    dates <- seq(as.Date(x = paste0(year, "-01-01")), by = "day", length.out = n_days)

    grid <- expand.grid(
      longitude = lons,
      latitude = lats,
      date = dates,
      KEEP.OUT.ATTRS = FALSE,
      stringsAsFactors = FALSE
    )

    grid$rainfall <- as.vector(rainfall)

    result_df <- grid[!is.na(grid$rainfall) & grid$rainfall > -900, ]
    rownames(result_df) <- NULL

    result_df
  }, finally = {
    nc_close(nc)
  })
}

#' Read an IMD rainfall NetCDF, cropped to a bbox at read time (fast path)
#'
#' Reads only the spatial hyperslab covering \code{bbox} directly off disk with
#' \code{ncvar_get(start, count)}, instead of materializing the whole national
#' grid and filtering afterwards. For a small region over many years this is
#' orders of magnitude faster and lighter (GB -> MB, minutes -> seconds).
#'
#' @param file_path Path to IMD NetCDF rainfall file.
#' @param year Year of the data (for the date axis).
#' @param bbox Named numeric vector/list with north, south, east, west.
#' @return data.frame with columns date, latitude, longitude, rainfall.
#' @keywords internal
read_imd_rainfall_cropped <- function(file_path, year, bbox) {
  north <- bbox[["north"]]
  south <- bbox[["south"]]
  east <- bbox[["east"]]
  west <- bbox[["west"]]

  nc <- nc_open(file_path)
  on.exit(nc_close(nc), add = TRUE)

  vars <- names(nc$var)
  latnm <- if ("LATITUDE" %in% names(nc$dim)) "LATITUDE" else "lat"
  lonnm <- if ("LONGITUDE" %in% names(nc$dim)) "LONGITUDE" else "lon"
  rainnm <- if ("RAINFALL" %in% vars) {
    "RAINFALL"
  } else if ("rf" %in% vars) {
    "rf"
  } else {
    setdiff(vars, c(latnm, lonnm, "TIME", "time"))[1]
  }

  lats <- as.numeric(nc$dim[[latnm]]$vals)
  lons <- as.numeric(nc$dim[[lonnm]]$vals)

  # IMD lon/lat are ascending, so min:max of the matches is a contiguous slab.
  li <- which(lats >= south & lats <= north)
  lj <- which(lons >= west & lons <= east)
  if (length(li) == 0L) li <- which.min(abs(lats - (south + north) / 2)) # bbox finer than grid
  if (length(lj) == 0L) lj <- which.min(abs(lons - (west + east) / 2))
  i0 <- min(li)
  ni <- max(li) - i0 + 1L
  j0 <- min(lj)
  nj <- max(lj) - j0 + 1L

  # dims are [LON, LAT, TIME]; collapse_degen=FALSE keeps single-cell axes so as.vector aligns.
  slab <- ncvar_get(nc, rainnm,
    start = c(j0, i0, 1L), count = c(nj, ni, -1L),
    collapse_degen = FALSE
  )

  sub_lons <- lons[j0:(j0 + nj - 1L)]
  sub_lats <- lats[i0:(i0 + ni - 1L)]
  n_days <- dim(slab)[3]
  dates <- seq(as.Date(paste0(year, "-01-01")), by = "day", length.out = n_days)

  df <- expand.grid(
    longitude = sub_lons, latitude = sub_lats, date = dates,
    KEEP.OUT.ATTRS = FALSE, stringsAsFactors = FALSE
  )
  df$rainfall <- as.vector(slab)
  df <- df[!is.na(df$rainfall) & df$rainfall > -900, c("date", "latitude", "longitude", "rainfall")]
  rownames(df) <- NULL
  df
}

#' Process multiple IMD files
#'
#' Reads and combines multiple IMD data files.
#'
#' @param file_paths Character vector of file paths.
#' @param var_type Variable type: "rain", "tmax", or "tmin".
#' @param resolution Resolution (for rainfall): 0.25 or 1.0.
#' @param years Integer vector. Years corresponding to each file.
#' @param bbox Optional named list/vector (north, south, east, west) passed to the
#'   rainfall reader to crop at read time; NULL reads the full grid (default).
#' @return A data.frame with columns `date`, `latitude`, `longitude` and the value column (`rainfall` or `temperature`), combining all files.
#' @export
#' @examplesIf interactive()
#' files <- download_imd_temperature(2023, 2024, var_type = "tmax")
#' data <- process_imd_files(files, "tmax", years = c(2023, 2024))
process_imd_files <- function(file_paths, var_type, resolution = NULL, years = NULL, bbox = NULL) {
  if (length(x = file_paths) == 0) stop("No files provided")

  years <- years %||% extract_years_from_filenames(file_paths)
  if (length(x = years) != length(x = file_paths)) stop("Number of years must match number of files")

  message(sprintf(fmt = "Processing %s IMD files", length(x = file_paths)))

  all_data <- lapply(seq_along(along.with = file_paths), function(i) {
    tryCatch(
      {
        if (var_type == "rain") {
          res <- resolution %||% if (grepl(pattern = "0.25", file_paths[i])) 0.25 else 1.0
          read_imd_rainfall(file_paths[i], res, years[i], bbox = bbox)
        } else if (var_type %in% c("tmax", "tmin")) {
          read_imd_temperature(file_paths[i], var_type, years[i])
        } else {
          stop("Invalid var_type: ", var_type)
        }
      },
      error = function(e) {
        stop(sprintf(fmt = "Error processing %s: %s", basename(path = file_paths[i]), e$message))
        NULL
      }
    )
  })

  all_data <- Filter(Negate(is.null), all_data)
  if (length(x = all_data) == 0) stop("No files were successfully processed")

  combined_df <- as.data.frame(data.table::rbindlist(all_data))
  combined_df <- combined_df[order(combined_df$date, combined_df$latitude, combined_df$longitude), ]
  rownames(combined_df) <- NULL

  message(sprintf(fmt = "Combined data: %s total data points", nrow(x = combined_df)))
  combined_df
}

#' Filter IMD data by spatial boundaries
#'
#' @param data data.frame with IMD data
#' @param north Northern latitude boundary
#' @param south Southern latitude boundary
#' @param east Eastern longitude boundary
#' @param west Western longitude boundary
#' @return The input data.frame restricted to rows whose `latitude`/`longitude` fall inside the region; columns are unchanged.
#' @export
#' @examples
#' imd <- data.frame(
#'   date = rep(as.Date("2023-01-01") + 0:59, each = 2),
#'   latitude = 20.5, longitude = c(73.5, 79.5), rainfall = 1
#' )
#' filter_imd_by_bbox(imd, north = 22, south = 18, east = 76, west = 72)
filter_imd_by_bbox <- function(data, north, south, east, west) {
  if (!all(c("latitude", "longitude") %in% names(data))) {
    stop("Data must contain 'latitude' and 'longitude' columns")
  }
  if (!validate_bbox(north, south, east, west)) stop("Invalid bounding box coordinates")

  filtered <- data[data$latitude >= south & data$latitude <= north &
    data$longitude >= west & data$longitude <= east, ]

  message(sprintf(fmt = "Filtered %s points to %s within bounding box", nrow(x = data), nrow(x = filtered)))
  filtered
}

#' Filter IMD data by GeoJSON polygon
#'
#' @param data data.frame with IMD data
#' @param geojson_file Path to GeoJSON file
#' @return The input data.frame restricted to rows whose `latitude`/`longitude` fall inside the region; columns are unchanged.
#' @export
#' @examples
#' imd <- data.frame(
#'   date = rep(as.Date("2023-01-01") + 0:59, each = 2),
#'   latitude = 20.5, longitude = c(73.5, 79.5), rainfall = 1
#' )
#' region <- system.file("extdata", "region.geojson", package = "varunayan")
#' filter_imd_by_geojson(imd, region)
filter_imd_by_geojson <- function(data, geojson_file) {
  if (!all(c("latitude", "longitude") %in% names(data))) {
    stop("Data must contain 'latitude' and 'longitude' columns")
  }

  # shared filter reorders rows; subset by row id to keep input order
  hit <- filter_dataframe_by_geojson(
    data.frame(latitude = data$latitude, longitude = data$longitude, row = seq_len(nrow(data))),
    geojson_file
  )
  data[sort(hit$row), , drop = FALSE]
}

#' Aggregate IMD data by temporal frequency
#'
#' @param data data.frame with IMD data
#' @param frequency Character string: "daily", "monthly", "yearly"
#' @return A data.frame with columns `date` (first day of each month or year), `latitude`, `longitude` and the value column, summed for rainfall and averaged for temperature. Returned unchanged when `frequency = "daily"`.
#' @export
#' @examples
#' imd <- data.frame(
#'   date = rep(as.Date("2023-01-01") + 0:59, each = 2),
#'   latitude = 20.5, longitude = c(73.5, 79.5), rainfall = 1
#' )
#' aggregate_imd_by_frequency(imd, "monthly")
aggregate_imd_by_frequency <- function(data, frequency = "daily") {
  if (!"date" %in% names(data)) stop("Data must contain 'date' column")
  freq <- tolower(x = frequency)
  if (freq == "daily") {
    return(data)
  }

  value_col <- setdiff(x = names(x = data), y = c("date", "latitude", "longitude"))[1]
  if (is.na(value_col)) stop("No value column found in data")

  agg_fun <- if (value_col == "rainfall") sum else mean
  DT <- as.data.table(data)
  DT[, date := as.Date(date)]
  DT[, date := date - (if (freq == "yearly") yday(date) else mday(date)) + 1L]
  aggregated <- DT[, .(value = agg_fun(get(..value_col), na.rm = TRUE)), by = .(date, latitude, longitude)]
  setorder(aggregated, date, latitude, longitude)
  setnames(aggregated, "value", value_col)
  aggregated <- as.data.frame(aggregated)

  message(sprintf(fmt = "Aggregated from %s to %s points (%s)", nrow(x = data), nrow(x = aggregated), frequency))
  aggregated
}

is_leap_year <- function(year) {
  (year %% 4 == 0 & year %% 100 != 0) | (year %% 400 == 0)
}

extract_years_from_filenames <- function(filenames) {
  years <- vapply(filenames, function(f) {
    matches <- regmatches(f, gregexpr("[0-9]{4}", f))[[1]]
    if (length(x = matches) > 0) as.integer(x = matches[length(x = matches)]) else NA_integer_
  }, integer(1))

  if (any(is.na(years))) stop("Could not extract years from all filenames")
  years
}
