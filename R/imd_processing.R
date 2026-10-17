#' Functions to process IMD data

#' Read IMD binary temperature file
#'
#' Reads IMD binary temperature data (maximum or minimum) and converts the data to a data.frame.
#'
#' @param file_path Path to the IMD binary file (.grd).
#' @param var_type Variable type: "tmax" or "tmin".
#' @param year Year of the data.
#' @return data.frame with columns: date, latitude, longitude, temperature
#' @export
#' @examples
#' \dontrun{
#' tmax_data <- read_imd_temperature("imd_tmax_1.0_2023.grd", "tmax", 2023)
#' }
read_imd_temperature <- function(file_path, var_type, year) {
  if (!file.exists(file_path)) stop("Cannot find the file: ", file_path)

  dataset_id <- paste0(var_type, "_1.0")
  grid_specs <- get_imd_grid_specs(dataset_id)

  message(sprintf(fmt = "Read of IMD %s data for %s", var_type, year))
  message(sprintf(fmt = "Grid: %sx%s points", grid_specs$nlat, grid_specs$nlon))

  n_days <- if (is_leap_year(year)) 366 else 365

  con <- file(file_path, "rb")
  tryCatch({
    n_values <- n_days * grid_specs$nlat * grid_specs$nlon
    raw_data <- readBin(con, "numeric", n = n_values, size = 4, endian = "little")

    if (length(x = raw_data) != n_values) {
      warning(sprintf(fmt = "Expected %s values, but found %s", n_values, length(x = raw_data)), call. = FALSE)
    }
  }, finally = {
    close(con)
  })

  dates <- seq(as.Date(x = paste0(year, "-01-01")), as.Date(x = paste0(year, "-12-31")), by = "day")

  lats <- seq(grid_specs$lat_start, grid_specs$lat_end, by = grid_specs$resolution)
  lons <- seq(grid_specs$lon_start, grid_specs$lon_end, by = grid_specs$resolution)

  if (length(x = lats) != grid_specs$nlat) {
    warning(sprintf(fmt = "Latitude grid mismatch: expected %s, found %s", grid_specs$nlat, length(x = lats)), call. = FALSE)
    lats <- lats[1:grid_specs$nlat]
  }
  if (length(x = lons) != grid_specs$nlon) {
    warning(sprintf(fmt = "Longitude grid mismatch: expected %s, found %s", grid_specs$nlon, length(x = lons)), call. = FALSE)
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

  # Remove missing values (99.9 for temperature)
  result_df <- grid[!is.na(grid$temperature) & grid$temperature < 99, ]
  rownames(result_df) <- NULL

  message(sprintf(fmt = "Processed %s data points", nrow(x = result_df)))
  result_df
}

#' Read IMD NetCDF rainfall file
#'
#' Reads IMD NetCDF rainfall data and converts the data to a data.frame.
#'
#' @param file_path Path to the IMD NetCDF file (.nc).
#' @param resolution Spatial resolution: 0.25 or 1.0.
#' @param year Year of the data.
#' @param bbox Optional named list or vector (north, south, east, west). If you
#'   set it, the function reads only that spatial slab from the disk (fast path).
#'   If NULL, the function reads the full grid.
#' @return data.frame with columns: date, latitude, longitude, rainfall
#' @export
#' @examples
#' \dontrun{
#' rain_data <- read_imd_rainfall("imd_rainfall_0.25_2023.nc", 0.25, 2023)
#' }
read_imd_rainfall <- function(file_path, resolution, year, bbox = NULL) {
  if (!file.exists(file_path)) stop("Cannot find the file: ", file_path)

  if (!is.null(bbox)) {
    return(read_imd_rainfall_cropped(file_path, year, bbox))
  }

  dataset_id <- paste0("rainfall_", resolution)
  grid_specs <- get_imd_grid_specs(dataset_id)

  message(sprintf(fmt = "Read of IMD rainfall data for %s", year))
  message(sprintf(fmt = "Resolution: %s\u00b0", resolution))

  rainfall_data <- tryCatch(
    read_ncdf(file_path),
    error = function(e) {
      warning(sprintf(fmt = "read_ncdf failed. The function will try ncdf4: %s", e$message), call. = FALSE)
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

    rain_vars <- c("rf", "rainfall", "rain", "precip")
    rain_col <- intersect(rain_vars, names(df))
    if (length(x = rain_col) == 0) {
      rain_col <- setdiff(x = names(x = df), y = c("longitude", "latitude", "date"))[1]
    } else {
      rain_col <- rain_col[1]
    }

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

#' Read IMD NetCDF with ncdf4
#'
#' @param file_path Path to the NetCDF file
#' @param grid_specs Grid specifications
#' @param year Year of the data
#' @return data.frame
#' @keywords internal
read_imd_rainfall_ncdf4 <- function(file_path, grid_specs, year) {
  nc <- nc_open(file_path)

  tryCatch({
    dims <- names(nc$dim)
    vars <- names(nc$var)

    message(sprintf(fmt = "NetCDF dimensions: %s", paste(dims, collapse = ", ")))
    message(sprintf(fmt = "NetCDF variables: %s", paste(vars, collapse = ", ")))

    lats <- ncvar_get(nc, "lat")
    lons <- ncvar_get(nc, "lon")

    rain_var <- if ("rf" %in% vars) "rf" else setdiff(vars, c("lat", "lon", "time"))[1]
    if (is.na(rain_var)) stop("Cannot find a rainfall variable in the NetCDF file")

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

#' Read only the bbox area of an IMD rainfall NetCDF file (fast path)
#'
#' Reads only the spatial hyperslab that contains \code{bbox} directly from the
#' disk with \code{ncvar_get(start, count)}. The function does not read the full
#' national grid into memory and then filter it. For a small region and many
#' years, this method is orders of magnitude faster. It also uses much less
#' memory (GB -> MB, minutes -> seconds).
#'
#' @param file_path Path to the IMD NetCDF rainfall file.
#' @param year Year of the data (for the date axis).
#' @param bbox Named numeric vector or list with north, south, east, and west.
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

  # IMD lon/lat values increase. Thus, min:max of the matches is a contiguous slab.
  li <- which(lats >= south & lats <= north)
  lj <- which(lons >= west & lons <= east)
  if (length(li) == 0L) li <- which.min(abs(lats - (south + north) / 2)) # bbox is smaller than one grid cell
  if (length(lj) == 0L) lj <- which.min(abs(lons - (west + east) / 2))
  i0 <- min(li)
  ni <- max(li) - i0 + 1L
  j0 <- min(lj)
  nj <- max(lj) - j0 + 1L

  # dims are [LON, LAT, TIME]. collapse_degen=FALSE keeps the single-cell axes.
  # Thus, as.vector gives the correct alignment.
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
#' @param years Integer vector. The year of each file.
#' @param bbox Optional named list or vector (north, south, east, west). The
#'   function sends it to the rainfall reader, which crops the grid at read time.
#'   If NULL, the function reads the full grid (default).
#' @return data.frame with the combined data.
#' @export
#' @examples
#' \dontrun{
#' files <- c("imd_tmax_1.0_2023.grd", "imd_tmax_1.0_2024.grd")
#' data <- process_imd_files(files, "tmax", years = c(2023, 2024))
#' }
process_imd_files <- function(file_paths, var_type, resolution = NULL, years = NULL, bbox = NULL) {
  if (length(x = file_paths) == 0) stop("The file list is empty")

  years <- years %||% extract_years_from_filenames(file_paths)
  if (length(x = years) != length(x = file_paths)) stop("The number of years must be equal to the number of files")

  message(sprintf(fmt = "IMD files to process: %s", length(x = file_paths)))

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
        stop(sprintf(fmt = "Cannot process %s: %s", basename(path = file_paths[i]), e$message))
        NULL
      }
    )
  })

  all_data <- Filter(Negate(is.null), all_data)
  if (length(x = all_data) == 0) stop("The process failed for all files")

  combined_df <- as.data.frame(data.table::rbindlist(all_data))
  combined_df <- combined_df[order(combined_df$date, combined_df$latitude, combined_df$longitude), ]
  rownames(combined_df) <- NULL

  message(sprintf(fmt = "Combined data: %s total data points", nrow(x = combined_df)))
  combined_df
}

#' Filter IMD data by spatial boundaries
#'
#' @param data data.frame with IMD data
#' @param north Latitude of the north boundary
#' @param south Latitude of the south boundary
#' @param east Longitude of the east boundary
#' @param west Longitude of the west boundary
#' @return Filtered data.frame
#' @export
filter_imd_by_bbox <- function(data, north, south, east, west) {
  if (!all(c("latitude", "longitude") %in% names(data))) {
    stop("Data must contain 'latitude' and 'longitude' columns")
  }
  if (!validate_bbox(north, south, east, west)) stop("Invalid bounding box coordinates")

  filtered <- data[data$latitude >= south & data$latitude <= north &
    data$longitude >= west & data$longitude <= east, ]

  message(sprintf(fmt = "Filtered %s points to %s in the bounding box", nrow(x = data), nrow(x = filtered)))
  filtered
}

#' Filter IMD data by GeoJSON polygon
#'
#' @param data data.frame with IMD data
#' @param geojson_file Path to the GeoJSON file
#' @return Filtered data.frame
#' @export
filter_imd_by_geojson <- function(data, geojson_file) {
  if (!all(c("latitude", "longitude") %in% names(data))) {
    stop("Data must contain 'latitude' and 'longitude' columns")
  }

  geojson_sf <- st_read(geojson_file, quiet = TRUE)
  if (is.na(st_crs(geojson_sf))) geojson_sf <- st_set_crs(geojson_sf, 4326)
  geojson_sf <- st_transform(geojson_sf, 4326)

  points_sf <- st_as_sf(data, coords = c("longitude", "latitude"), crs = 4326)
  inside <- apply(st_within(points_sf, geojson_sf, sparse = FALSE), 1, any)
  filtered <- data[inside, ]

  message(sprintf(fmt = "Filtered %s points to %s in the GeoJSON boundary", nrow(x = data), nrow(x = filtered)))
  filtered
}

#' Aggregate IMD data by temporal frequency
#'
#' @param data data.frame with IMD data
#' @param frequency Character string: "daily", "monthly", "yearly"
#' @return Aggregated data.frame
#' @export
aggregate_imd_by_frequency <- function(data, frequency = "daily") {
  if (!"date" %in% names(data)) stop("Data must contain a 'date' column")
  if (tolower(x = frequency) == "daily") {
    return(data)
  }

  value_col <- setdiff(x = names(x = data), y = c("date", "latitude", "longitude"))[1]
  if (is.na(value_col)) stop("Cannot find a value column in the data")

  if (requireNamespace("data.table", quietly = TRUE)) {
    DT <- as.data.table(data)

    freq_lower <- tolower(x = frequency)
    if (freq_lower == "monthly") {
      DT[, time_group := year(date) * 100L + month(date)]
    } else if (freq_lower == "yearly") {
      DT[, time_group := year(date)]
    } else {
      DT[, time_group := year(date) * 100L + month(date)]
    }

    agg_fun <- if (value_col == "rainfall") sum else mean

    aggregated <- DT[, .(value = agg_fun(get(..value_col), na.rm = TRUE)),
      by = .(time_group, latitude, longitude)
    ]

    if (freq_lower == "monthly") {
      aggregated[, date := as.Date(paste0(
        time_group %/% 100L, "-",
        sprintf(fmt = "%02d", time_group %% 100L), "-01"
      ))]
    } else if (freq_lower == "yearly") {
      aggregated[, date := as.Date(x = paste0(time_group, "-01-01"))]
    } else {
      aggregated[, date := as.Date(paste0(
        time_group %/% 100L, "-",
        sprintf(fmt = "%02d", time_group %% 100L), "-01"
      ))]
    }

    setorder(aggregated, date, latitude, longitude)

    aggregated[, time_group := NULL]
    setnames(aggregated, "value", value_col)

    aggregated <- as.data.frame(aggregated)
  } else {
    freq_lower <- tolower(x = frequency)
    data$time_group <- format(data$date, switch(freq_lower,
      monthly = "%Y-%m",
      yearly = "%Y",
      "%Y-%m"
    ))

    agg_fun <- if (value_col == "rainfall") sum else mean
    formula_str <- paste(value_col, "~ time_group + latitude + longitude")

    aggregated <- aggregate(
      as.formula(formula_str),
      data = data,
      FUN = agg_fun,
      na.rm = TRUE
    )

    if (freq_lower == "yearly") {
      aggregated$date <- as.Date(x = paste0(aggregated$time_group, "-01-01"))
    } else {
      aggregated$date <- as.Date(x = paste0(aggregated$time_group, "-01"))
    }
    aggregated$time_group <- NULL

    aggregated <- aggregated[, c("date", "latitude", "longitude", value_col)]
    aggregated <- aggregated[order(aggregated$date, aggregated$latitude, aggregated$longitude), ]
    rownames(aggregated) <- NULL
  }

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

  if (any(is.na(years))) stop("Cannot extract the years from all the filenames")
  years
}
