#' Download and process IMD rainfall data for a bounding box
#'
#' Downloads IMD gridded rainfall data and keeps only the data in the specified bounding box.
#'
#' @param request_id Unique identifier for the request.
#' @param start_year Start year.
#' @param end_year End year.
#' @param north Latitude of the north boundary.
#' @param south Latitude of the south boundary.
#' @param east Longitude of the east boundary.
#' @param west Longitude of the west boundary.
#' @param resolution Spatial resolution: 0.25 or 1.0 degrees (default: 0.25).
#' @param frequency Temporal frequency: "daily", "monthly", "yearly" (default: "daily").
#' @param save_raw If TRUE, keep the raw downloaded files (default: FALSE).
#' @param output_dir Directory for the output files (default: tempdir()).
#' @param use_cache If TRUE, use the cached data when it is available (default: TRUE).
#' @param ... Arguments that the aliases send to the primary function.
#' @return A data.frame with columns `date`, `latitude`, `longitude` and `rainfall` (mm), restricted to the requested region and aggregated to `frequency`.
#' @export
#' @examplesIf interactive()
#' data <- imd_rainfall_bbox(
#'   request_id = "maharashtra_rain",
#'   start_year = 2023,
#'   end_year = 2024,
#'   north = 22, south = 16,
#'   east = 80, west = 73,
#'   resolution = 0.25,
#'   frequency = "monthly"
#' )
imd_rainfall_bbox <- function(request_id, start_year, end_year,
                              north, south, east, west,
                              resolution = 0.25, frequency = "daily",
                              save_raw = FALSE, output_dir = tempdir(),
                              use_cache = TRUE) {
  message("=== IMD Rainfall: Download and Process ===")
  message(sprintf(fmt = "Request ID: %s", request_id))
  message(sprintf(fmt = "Years: %s to %s", start_year, end_year))
  message(sprintf(fmt = "Resolution: %s\u00b0", resolution))
  message(sprintf(fmt = "Bounding box: N:%s, S:%s, E:%s, W:%s", north, south, east, west))

  if (!validate_bbox(north, south, east, west)) {
    stop("Invalid bounding box coordinates")
  }

  downloaded_files <- download_imd_rainfall(
    start_year = start_year,
    end_year = end_year,
    resolution = resolution,
    output_dir = output_dir,
    use_cache = use_cache
  )

  if (length(x = downloaded_files) == 0) stop("All file downloads failed")

  years <- start_year:end_year
  processed_data <- process_imd_files(
    file_paths = downloaded_files,
    var_type = "rain",
    resolution = resolution,
    years = years,
    bbox = list(north = north, south = south, east = east, west = west)
  )

  filtered_data <- filter_imd_by_bbox(
    data = processed_data,
    north = north, south = south,
    east = east, west = west
  )

  if (frequency != "daily") {
    filtered_data <- aggregate_imd_by_frequency(filtered_data, frequency)
  }

  save_imd_results(
    data = filtered_data,
    request_id = request_id,
    var_type = "rainfall",
    resolution = resolution,
    frequency = frequency,
    output_dir = output_dir
  )

  if (!save_raw) {
    unlink(downloaded_files)
    message("Deleted the raw downloaded files")
  }

  message("Process completed!")
  message(sprintf(fmt = "Final dataset: %s data points", nrow(x = filtered_data)))

  filtered_data
}

#' Download and process IMD rainfall for a single point (nearest grid cell)
#'
#' Extracts the daily rainfall series for the IMD grid cell that is nearest to
#' a (lat, lon) point. For each year, the function reads only that one cell from
#' the disk. Thus, this function is the method with the lowest cost to get a long
#' series for one location.
#'
#' @param request_id Unique identifier for the request.
#' @param start_year Start year (1901-2024).
#' @param end_year End year (1901-2024).
#' @param latitude Latitude of the point.
#' @param longitude Longitude of the point.
#' @param resolution Spatial resolution: 0.25 or 1.0 degrees (default: 0.25).
#' @param frequency Temporal frequency: "daily", "monthly", "yearly" (default: "daily").
#' @param save_raw If TRUE, keep the raw downloaded files (default: FALSE).
#' @param output_dir Directory for the output files (default: tempdir()).
#' @param use_cache If TRUE, use the cached data when it is available (default: TRUE).
#' @param ... Arguments that the aliases send to the primary function.
#' @return data.frame with the rainfall series of the nearest cell.
#' @export
#' @examples
#' \donttest{
#' powai <- tryCatch(
#'   imd_rainfall_point("powai", 2023, 2023, 19.1277, 72.9047,
#'     resolution = 1, use_cache = FALSE
#'   ),
#'   error = function(e) message("IMD server unavailable: ", conditionMessage(e))
#' )
#' }
imd_rainfall_point <- function(request_id, start_year, end_year,
                               latitude, longitude,
                               resolution = 0.25, frequency = "daily",
                               save_raw = FALSE, output_dir = tempdir(),
                               use_cache = TRUE) {
  message("=== IMD Rainfall: Download and Process (point) ===")
  message(sprintf(fmt = "Request ID: %s", request_id))
  message(sprintf(fmt = "Point: lat %.4f, lon %.4f", latitude, longitude))

  downloaded_files <- download_imd_rainfall(
    start_year = start_year, end_year = end_year,
    resolution = resolution, output_dir = output_dir, use_cache = use_cache
  )
  if (length(x = downloaded_files) == 0) stop("All file downloads failed")

  pt_bbox <- list(north = latitude, south = latitude, east = longitude, west = longitude)
  data <- process_imd_files(
    file_paths = downloaded_files, var_type = "rain",
    resolution = resolution, years = start_year:end_year, bbox = pt_bbox
  )

  i <- which.min((data$latitude - latitude)^2 + (data$longitude - longitude)^2)
  near_lat <- data$latitude[i]
  near_lon <- data$longitude[i]
  data <- data[data$latitude == near_lat & data$longitude == near_lon, ]
  message(sprintf(fmt = "Nearest cell: lat %.3f, lon %.3f", near_lat, near_lon))

  if (frequency != "daily") data <- aggregate_imd_by_frequency(data, frequency)

  save_imd_results(
    data = data, request_id = request_id, var_type = "rainfall",
    resolution = resolution, frequency = frequency, output_dir = output_dir
  )

  if (!save_raw) {
    unlink(downloaded_files)
    message("Deleted the raw downloaded files")
  }
  message(sprintf(fmt = "Final dataset: %s data points", nrow(x = data)))
  data
}

#' Download and process IMD rainfall data for a GeoJSON region
#'
#' @param request_id Unique identifier for the request.
#' @param start_year Start year (1901-2025).
#' @param end_year End year (1901-2025).
#' @param geojson_file Path to the GeoJSON file.
#' @param resolution Spatial resolution: 0.25 or 1.0 degrees (default: 0.25).
#' @param frequency Temporal frequency (default: "daily").
#' @param save_raw If TRUE, keep the raw files (default: FALSE).
#' @param output_dir Directory for the output files (default: tempdir()).
#' @param use_cache If TRUE, use the cached data when it is available (default: TRUE).
#' @param ... Arguments that the aliases send to the primary function.
#' @return A data.frame with columns `date`, `latitude`, `longitude` and `rainfall` (mm), restricted to the requested region and aggregated to `frequency`.
#' @export
#' @examplesIf interactive()
#' region <- system.file("extdata", "region.geojson", package = "varunayan")
#' data <- imd_rainfall_geojson(
#'   request_id = "mh_rain", start_year = 2023, end_year = 2023,
#'   geojson_file = region, frequency = "monthly"
#' )
imd_rainfall_geojson <- function(request_id, start_year, end_year, geojson_file,
                                 resolution = 0.25, frequency = "daily",
                                 save_raw = FALSE, output_dir = tempdir(),
                                 use_cache = TRUE) {
  message("=== IMD Rainfall: Download and Process ===")
  message(sprintf(fmt = "Request ID: %s", request_id))
  message(sprintf(fmt = "GeoJSON: %s", basename(path = geojson_file)))

  if (!file.exists(geojson_file)) {
    stop("Cannot find the GeoJSON file: ", geojson_file)
  }

  geojson_sf <- st_read(geojson_file, quiet = TRUE)
  bbox <- st_bbox(geojson_sf)

  north <- bbox[["ymax"]]
  south <- bbox[["ymin"]]
  east <- bbox[["xmax"]]
  west <- bbox[["xmin"]]

  message(sprintf(fmt = "Bounding box from GeoJSON: N:%s, S:%s, E:%s, W:%s", round(north, 2), round(south, 2), round(east, 2), round(west, 2)))

  downloaded_files <- download_imd_rainfall(
    start_year = start_year,
    end_year = end_year,
    resolution = resolution,
    output_dir = output_dir,
    use_cache = use_cache
  )

  if (length(x = downloaded_files) == 0) stop("All file downloads failed")

  years <- start_year:end_year
  processed_data <- process_imd_files(
    file_paths = downloaded_files,
    var_type = "rain",
    resolution = resolution,
    years = years,
    bbox = list(north = north, south = south, east = east, west = west)
  )

  filtered_data <- filter_imd_by_geojson(
    data = processed_data,
    geojson_file = geojson_file
  )

  if (frequency != "daily") {
    filtered_data <- aggregate_imd_by_frequency(filtered_data, frequency)
  }

  save_imd_results(
    data = filtered_data,
    request_id = request_id,
    var_type = "rainfall",
    resolution = resolution,
    frequency = frequency,
    output_dir = output_dir
  )

  if (!save_raw) {
    unlink(downloaded_files)
    message("Deleted the raw downloaded files")
  }

  message("Process completed!")
  message(sprintf(fmt = "Final dataset: %s data points", nrow(x = filtered_data)))

  filtered_data
}

#' Download and process IMD temperature data for a bounding box
#'
#' @param request_id Unique identifier for the request.
#' @param start_year Start year (1951-2025).
#' @param end_year End year (1951-2025).
#' @param north Latitude of the north boundary.
#' @param south Latitude of the south boundary.
#' @param east Longitude of the east boundary.
#' @param west Longitude of the west boundary.
#' @param var_type Temperature type: "tmax" or "tmin".
#' @param frequency Temporal frequency (default: "daily").
#' @param save_raw If TRUE, keep the raw files (default: FALSE).
#' @param output_dir Directory for the output files (default: tempdir()).
#' @param use_cache If TRUE, use the cached data when it is available (default: TRUE).
#' @param ... Arguments that the aliases send to the primary function.
#' @return A data.frame with columns `date`, `latitude`, `longitude` and `temperature` (degrees Celsius), restricted to the requested region and aggregated to `frequency`.
#' @export
#' @examplesIf interactive()
#' data <- imd_temperature_bbox(
#'   request_id = "delhi_tmax",
#'   start_year = 2023,
#'   end_year = 2024,
#'   north = 29, south = 28,
#'   east = 78, west = 76,
#'   var_type = "tmax"
#' )
imd_temperature_bbox <- function(request_id, start_year, end_year,
                                 north, south, east, west,
                                 var_type = "tmax", frequency = "daily",
                                 save_raw = FALSE, output_dir = tempdir(),
                                 use_cache = TRUE) {
  message("=== IMD Temperature: Download and Process ===")
  message(sprintf(fmt = "Request ID: %s", request_id))
  message(sprintf(fmt = "Variable: %s", var_type))
  message(sprintf(fmt = "Years: %s to %s", start_year, end_year))

  if (!validate_bbox(north, south, east, west)) {
    stop("Invalid bounding box coordinates")
  }

  downloaded_files <- download_imd_temperature(
    start_year = start_year,
    end_year = end_year,
    var_type = var_type,
    output_dir = output_dir,
    use_cache = use_cache
  )

  if (length(x = downloaded_files) == 0) stop("All file downloads failed")

  years <- start_year:end_year
  processed_data <- process_imd_files(
    file_paths = downloaded_files,
    var_type = var_type,
    years = years
  )

  filtered_data <- filter_imd_by_bbox(
    data = processed_data,
    north = north, south = south,
    east = east, west = west
  )

  if (frequency != "daily") {
    filtered_data <- aggregate_imd_by_frequency(filtered_data, frequency)
  }

  save_imd_results(
    data = filtered_data,
    request_id = request_id,
    var_type = var_type,
    resolution = 1.0,
    frequency = frequency,
    output_dir = output_dir
  )

  if (!save_raw) {
    unlink(downloaded_files)
    message("Deleted the raw downloaded files")
  }

  message("Process completed!")
  message(sprintf(fmt = "Final dataset: %s data points", nrow(x = filtered_data)))

  filtered_data
}

#' Download and process IMD temperature data for a GeoJSON region
#'
#' @param request_id Unique identifier for the request.
#' @param start_year Start year (1951-2025).
#' @param end_year End year (1951-2025).
#' @param geojson_file Path to the GeoJSON file.
#' @param var_type Temperature type: "tmax" or "tmin".
#' @param frequency Temporal frequency (default: "daily").
#' @param save_raw If TRUE, keep the raw files (default: FALSE).
#' @param output_dir Directory for the output files (default: tempdir()).
#' @param use_cache If TRUE, use the cached data when it is available (default: TRUE).
#' @param ... Arguments that the aliases send to the primary function.
#' @return A data.frame with columns `date`, `latitude`, `longitude` and `temperature` (degrees Celsius), restricted to the requested region and aggregated to `frequency`.
#' @export
#' @examplesIf interactive()
#' region <- system.file("extdata", "region.geojson", package = "varunayan")
#' data <- imd_temperature_geojson(
#'   request_id = "mh_tmax", start_year = 2023, end_year = 2023,
#'   geojson_file = region, var_type = "tmax", frequency = "monthly"
#' )
imd_temperature_geojson <- function(request_id, start_year, end_year, geojson_file,
                                    var_type = "tmax", frequency = "daily",
                                    save_raw = FALSE, output_dir = tempdir(),
                                    use_cache = TRUE) {
  message("=== IMD Temperature: Download and Process ===")
  message(sprintf(fmt = "Request ID: %s", request_id))
  message(sprintf(fmt = "Variable: %s", var_type))
  message(sprintf(fmt = "GeoJSON: %s", basename(path = geojson_file)))

  if (!file.exists(geojson_file)) {
    stop("Cannot find the GeoJSON file: ", geojson_file)
  }

  downloaded_files <- download_imd_temperature(
    start_year = start_year,
    end_year = end_year,
    var_type = var_type,
    output_dir = output_dir,
    use_cache = use_cache
  )

  if (length(x = downloaded_files) == 0) stop("All file downloads failed")

  years <- start_year:end_year
  processed_data <- process_imd_files(
    file_paths = downloaded_files,
    var_type = var_type,
    years = years
  )

  filtered_data <- filter_imd_by_geojson(
    data = processed_data,
    geojson_file = geojson_file
  )

  if (frequency != "daily") {
    filtered_data <- aggregate_imd_by_frequency(filtered_data, frequency)
  }

  save_imd_results(
    data = filtered_data,
    request_id = request_id,
    var_type = var_type,
    resolution = 1.0,
    frequency = frequency,
    output_dir = output_dir
  )

  if (!save_raw) {
    unlink(downloaded_files)
    message("Deleted the raw downloaded files")
  }

  message("Process completed!")
  message(sprintf(fmt = "Final dataset: %s data points", nrow(x = filtered_data)))

  filtered_data
}

#' Save IMD results to CSV
#'
#' @param data data.frame with the processed data
#' @param request_id Request identifier
#' @param var_type Variable type
#' @param resolution Resolution
#' @param frequency Frequency
#' @param output_dir Output directory
#' @noRd
save_imd_results <- function(data, request_id, var_type, resolution, frequency, output_dir) {
  imd_output_dir <- file.path(output_dir, paste0(request_id, "_imd_output"))
  ensure_output_dir(imd_output_dir)

  output_file <- file.path(
    imd_output_dir,
    sprintf(fmt = "%s_imd_%s_%s_%s_data.csv", request_id, var_type, resolution, frequency)
  )

  write.csv(data, output_file, row.names = FALSE)
  message(sprintf(fmt = "Saved data to: %s", output_file))

  unique_coords <- unique(x = data[, c("latitude", "longitude")])
  coords_file <- file.path(imd_output_dir, sprintf(fmt = "%s_unique_coordinates.csv", request_id))
  write.csv(unique_coords, coords_file, row.names = FALSE)
  message(sprintf(fmt = "Saved %s unique coordinates to: %s", nrow(x = unique_coords), coords_file))

  metadata <- list(
    request_id = request_id,
    var_type = var_type,
    resolution = resolution,
    frequency = frequency,
    n_records = nrow(x = data),
    n_locations = nrow(x = unique_coords),
    date_range = c(min(data$date), max(data$date)),
    spatial_extent = c(
      min(data$latitude), max(data$latitude),
      min(data$longitude), max(data$longitude)
    ),
    created_at = Sys.time()
  )

  metadata_file <- file.path(imd_output_dir, sprintf(fmt = "%s_metadata.json", request_id))
  write_json(metadata, metadata_file, pretty = TRUE, auto_unbox = TRUE)
  message(sprintf(fmt = "Saved metadata to: %s", metadata_file))

  invisible(output_file)
}

#' Download IMD temperature aggregated for each GeoJSON feature (region x time)
#'
#' [imd_temperature_geojson()] returns the grid points in the GeoJSON boundary.
#' This function is different. It returns one row for each feature (for example,
#' each state) and each time period. Each row contains the mean temperature of
#' the region.
#'
#' @param request_id Unique identifier for the request.
#' @param start_year Start year (>= 1951).
#' @param end_year End year (<= 2024).
#' @param geojson_file Path to a GeoJSON file. Each feature in the file is one region.
#' @param feature_col Name of the GeoJSON property that sets the groups (for
#'   example, `"state_name"`). If NULL, the function uses the first column that
#'   is not the geometry column.
#' @param var_type `"tmax"`, `"tmin"`, or `"tmean"` (mean of tmax and tmin).
#'   The default is `"tmean"`.
#' @param frequency `"monthly"` (default), `"yearly"`, or `"daily"`.
#' @param use_cache If TRUE, use the cached IMD downloads when they are available (default TRUE).
#' @return A data.frame with the columns `region`, `year`, `month` (only for monthly data), and `temperature`.
#' @export
#' @examples
#' \donttest{
#' temp <- tryCatch(
#'   imd_temperature_by_region(
#'     request_id = "demo_region",
#'     start_year = 2023, end_year = 2023,
#'     geojson_file = system.file("extdata", "region.geojson", package = "varunayan"),
#'     var_type = "tmax", frequency = "monthly", use_cache = FALSE
#'   ),
#'   error = function(e) message("IMD server unavailable: ", conditionMessage(e))
#' )
#' }
imd_temperature_by_region <- function(request_id, start_year, end_year,
                                      geojson_file, feature_col = NULL,
                                      var_type = "tmean", frequency = "monthly",
                                      use_cache = TRUE) {
  stopifnot(var_type %in% c("tmax", "tmin", "tmean"))
  local_s2_off()

  regions <- sf::st_make_valid(sf::st_read(geojson_file, quiet = TRUE))
  if (is.null(feature_col)) {
    feature_col <- setdiff(names(regions), attr(regions, "sf_column"))[1]
  }

  read_all <- function(vt) {
    files <- download_imd_temperature(start_year, end_year,
      var_type = vt,
      use_cache = use_cache
    )
    yrs <- start_year:end_year
    do.call(rbind, Map(function(f, y) read_imd_temperature(f, vt, y), files, yrs))
  }

  if (var_type %in% c("tmax", "tmin")) {
    raw <- read_all(var_type)
  } else {
    tmax_raw <- read_all("tmax")
    tmin_raw <- read_all("tmin")
    raw <- merge(tmax_raw, tmin_raw,
      by = c("longitude", "latitude", "date"),
      suffixes = c("_max", "_min")
    )
    raw$temperature <- (raw$temperature_max + raw$temperature_min) / 2
  }
  d <- as.Date(raw$date)
  raw$year <- as.integer(format(d, "%Y"))
  grp <- switch(frequency,
    monthly = {
      raw$month <- as.integer(format(d, "%m"))
      c("year", "month")
    },
    yearly = "year",
    {
      raw$date <- d
      "date"
    }
  )
  out <- aggregate_to_polygons(raw, regions, "temperature",
    method = "point_in_polygon", polygon_id_cols = feature_col, by = grp
  )
  names(out)[names(out) == feature_col] <- "region"
  # A region with no grid cell has no row, as before.
  out <- out[!is.na(out$temperature), ]
  out[order(out$region, out$year), ]
}
