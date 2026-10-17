#' Spatial utilities that aggregate gridded data to polygons

#' Aggregate gridded data to polygon regions
#'
#' Assigns each grid cell to a polygon, then aggregates the values of the
#' cells in each polygon. The spatial match uses only the distinct cells.
#' Thus, a daily series with many dates does not make the match slower.
#'
#' @param data Data frame with longitude, latitude, and value columns
#' @param polygons sf object with polygon geometries (CRS 4326)
#' @param value_col Name of the column to aggregate, or a character vector
#'   of names. Give names to set the result columns, for example
#'   `c(tmean = "temp_c")`. A column without a name keeps its name.
#' @param method Aggregation method: `"nearest_centroid"` (each polygon gets
#'   the cell nearest to a point on its surface) or `"point_in_polygon"` (each
#'   polygon gets the cells in it)
#' @param polygon_id_cols Character vector of column names to use as polygon
#'   identifiers. The default is all the columns of `polygons` except the
#'   geometry.
#' @param agg_fun Aggregation function. It gets the values of one group,
#'   which can include `NA`. The default is the mean without the `NA` values.
#' @param by Optional character vector of more group columns in `data`, for
#'   example `"date"`. The result then has one row for each polygon and each
#'   value of `by`.
#' @param fill_empty For `"point_in_polygon"`: if `TRUE`, a polygon with no
#'   cell in it (smaller than a cell) gets the cell nearest to a point on its
#'   surface.
#' @return Data frame with the polygon identifiers, the `by` columns and the
#'   aggregated values. It has one row for each polygon and each value of
#'   `by`. A polygon with no cell has `NA`.
#' @export
#' @examples
#' if (requireNamespace("sf", quietly = TRUE)) {
#'   square <- function(x0) sf::st_polygon(list(rbind(c(x0, 0), c(x0 + 1, 0), c(x0 + 1, 1), c(x0, 1), c(x0, 0))))
#'   polygons <- sf::st_sf(id = c("a", "b"), geometry = sf::st_sfc(square(0), square(1), crs = 4326))
#'   grid <- expand.grid(longitude = c(0.25, 0.75, 1.25, 1.75), latitude = 0.5, date = as.Date("2020-01-01") + 0:1)
#'   grid$temp <- seq_len(nrow(grid))
#'   aggregate_to_polygons(grid, polygons, "temp", method = "point_in_polygon", by = "date")
#' }
aggregate_to_polygons <- function(data, polygons, value_col,
                                  method = c("nearest_centroid", "point_in_polygon"),
                                  polygon_id_cols = NULL,
                                  agg_fun = function(x) mean(x, na.rm = TRUE),
                                  by = NULL,
                                  fill_empty = FALSE) {
  method <- match.arg(method)

  if (!requireNamespace("sf", quietly = TRUE)) {
    stop("Package 'sf' is necessary for spatial operations")
  }

  if (is.null(polygon_id_cols)) {
    polygon_id_cols <- setdiff(names(polygons), attr(polygons, "sf_column"))
  }

  local_s2_off()

  vals <- unname(value_col)
  # setDT on a list of the needed columns does not copy the input data.
  dt <- data.table::setDT(as.list(data)[c("longitude", "latitude", by, vals)])
  cells <- as.data.frame(unique(dt[, c("longitude", "latitude"), with = FALSE]))
  key <- data.table::as.data.table(grid_polygon_key(cells, polygons, polygon_id_cols, method, fill_empty))
  result <- dt[key, on = c("longitude", "latitude"), nomatch = NULL, allow.cartesian = TRUE][
    , lapply(.SD, agg_fun),
    by = c(polygon_id_cols, by), .SDcols = vals
  ]

  # Give a row to each polygon and each value of `by`, also when the polygon has no cell.
  full <- unique(sf::st_drop_geometry(polygons)[polygon_id_cols])
  if (!is.null(by)) full <- merge(full, unique(dt[, by, with = FALSE]), by = NULL)
  result <- result[data.table::as.data.table(full), on = c(polygon_id_cols, by)]

  out_names <- names(value_col) %||% vals
  out_names[out_names == ""] <- vals[out_names == ""]
  data.table::setnames(result, vals, out_names)
  return(as.data.frame(result))
}

#' Match grid cells to polygons
#' @return Data frame with longitude, latitude and the polygon identifiers.
#'   A cell can match more than one polygon.
#' @noRd
grid_polygon_key <- function(cells, polygons, polygon_id_cols, method, fill_empty) {
  pts <- sf::st_as_sf(cells, coords = c("longitude", "latitude"), crs = 4326)
  geom <- sf::st_geometry(polygons)
  # A point on the surface is in the polygon. A centroid can be outside a concave polygon.
  # When s2 is off, sf warns that the point is approximate for lon/lat data. For the nearest cell, this approximation is sufficient.
  # With s2 off, sf also writes a message that st_contains() and st_nearest_feature() use planar coordinates.
  # For grid cells of 0.25 degrees or more, this is the intended method.
  nearest_cell <- function(g) {
    as.list(suppressMessages(sf::st_nearest_feature(suppressWarnings(sf::st_point_on_surface(g)), pts)))
  }
  hits <- if (method == "nearest_centroid") nearest_cell(geom) else suppressMessages(sf::st_contains(geom, pts))
  empty <- lengths(hits) == 0
  if (fill_empty && any(empty)) {
    hits[empty] <- nearest_cell(geom[empty])
  }
  poly <- rep(seq_along(hits), lengths(hits))
  cbind(cells[unlist(hits), ], sf::st_drop_geometry(polygons)[poly, polygon_id_cols, drop = FALSE])
}

#' Show the overlap of grid points and polygons
#'
#' @param grid_data Data frame with longitude and latitude columns, or the path to a NetCDF or CSV file
#' @param polygons sf object, or the path to a GeoJSON file
#' @param show_centroids Logical. If TRUE, show the polygon centroids
#' @param grid_color Color for grid points
#' @param polygon_fill Fill color for polygons
#' @param polygon_color Border color for polygons
#' @param centroid_color Color for centroids
#' @param title Plot title
#' @return ggplot object
#' @export
visualize_grid_overlap <- function(grid_data, polygons,
                                   show_centroids = TRUE,
                                   grid_color = "#E74C3C",
                                   polygon_fill = NA,
                                   polygon_color = "#2C3E50",
                                   centroid_color = "#3498DB",
                                   title = "Grid-Polygon Overlap") {
  if (!requireNamespace("sf", quietly = TRUE)) {
    stop("Package 'sf' is necessary")
  }

  if (!requireNamespace("ggplot2", quietly = TRUE)) {
    stop("Package 'ggplot2' is necessary")
  }

  if (is.character(polygons)) {
    polygons <- sf::st_read(polygons, quiet = TRUE)
  }

  if (is.character(grid_data)) {
    if (grepl("\\.nc$", grid_data, ignore.case = TRUE)) {
      stop("The function does not support NetCDF input at this time. Use a data frame.")
    } else {
      grid_data <- utils::read.csv(grid_data)
    }
  }

  grid_pts <- grid_data %>%
    dplyr::distinct(longitude, latitude)

  grid_sf <- sf::st_as_sf(grid_pts, coords = c("longitude", "latitude"), crs = 4326)

  p <- ggplot2::ggplot() +
    ggplot2::geom_sf(data = polygons, fill = polygon_fill, color = polygon_color, linewidth = 0.3) +
    ggplot2::geom_sf(data = grid_sf, color = grid_color, size = 1, alpha = 0.7)

  if (show_centroids) {
    local_s2_off()
    centroids <- suppressWarnings(sf::st_centroid(sf::st_geometry(polygons)))
    p <- p + ggplot2::geom_sf(data = centroids, color = centroid_color, size = 0.8, shape = 4)
  }

  p <- p +
    ggplot2::labs(
      title = title,
      subtitle = sprintf("Grid points: %d | Polygons: %d", nrow(grid_pts), nrow(polygons))
    ) +
    ggplot2::theme_minimal() +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "bold"),
      panel.grid = ggplot2::element_line(color = "grey90")
    )

  return(p)
}

#' Compare two or more grids
#'
#' @param ... Named data frames with longitude and latitude columns
#' @param polygons Optional sf object to show polygon boundaries
#' @param colors Named vector of colors for each grid
#' @param shapes Named vector of point shapes for each grid
#' @param point_size Size of grid points
#' @param polygon_color Color for polygon boundaries
#' @param title Plot title
#' @return ggplot object
#' @export
compare_grids <- function(..., polygons = NULL, colors = NULL, shapes = NULL,
                          point_size = 1, polygon_color = "#2C3E50",
                          title = "Grid Comparison") {
  if (!requireNamespace("sf", quietly = TRUE)) {
    stop("Package 'sf' is necessary")
  }
  if (!requireNamespace("ggplot2", quietly = TRUE)) {
    stop("Package 'ggplot2' is necessary")
  }

  grids <- list(...)
  grid_names <- names(grids)

  if (is.null(grid_names) || any(grid_names == "")) {
    stop("Give a name to each grid (for example, compare_grids(IMD = imd_data, ERA5 = era5_data))")
  }

  if (is.null(colors)) {
    default_colors <- c("#E74C3C", "#3498DB", "#27AE60", "#9B59B6", "#F39C12")
    colors <- setNames(default_colors[seq_along(grids)], grid_names)
  }

  if (is.null(shapes)) {
    default_shapes <- c(16, 16, 16, 16, 16)
    shapes <- setNames(default_shapes[seq_along(grids)], grid_names)
  }

  grid_pts_list <- lapply(grid_names, function(name) {
    df <- grids[[name]] %>%
      dplyr::distinct(longitude, latitude) %>%
      dplyr::mutate(grid = name)
    df
  })

  all_pts <- dplyr::bind_rows(grid_pts_list)
  all_pts$grid <- factor(all_pts$grid, levels = grid_names)

  p <- ggplot2::ggplot()

  if (!is.null(polygons)) {
    if (is.character(polygons)) {
      polygons <- sf::st_read(polygons, quiet = TRUE)
    }
    p <- p + ggplot2::geom_sf(data = polygons, fill = NA, color = polygon_color, linewidth = 0.2)
  }

  p <- p +
    ggplot2::geom_point(
      data = all_pts,
      ggplot2::aes(x = longitude, y = latitude, color = grid, shape = grid),
      size = point_size, alpha = 0.7
    ) +
    ggplot2::scale_color_manual(values = colors, name = "Grid") +
    ggplot2::scale_shape_manual(values = shapes, name = "Grid") +
    ggplot2::labs(title = title) +
    ggplot2::theme_minimal() +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "bold"),
      legend.position = "bottom"
    )

  if (!is.null(polygons)) {
    bbox <- sf::st_bbox(polygons)
    p <- p + ggplot2::coord_sf(
      xlim = c(bbox["xmin"], bbox["xmax"]),
      ylim = c(bbox["ymin"], bbox["ymax"])
    )
  } else {
    p <- p + ggplot2::coord_fixed()
  }

  counts <- sapply(grid_names, function(n) nrow(grids[[n]] %>% dplyr::distinct(longitude, latitude)))
  subtitle <- paste(sapply(grid_names, function(n) sprintf("%s: %d pts", n, counts[n])), collapse = " | ")
  p <- p + ggplot2::labs(subtitle = subtitle)

  return(p)
}

#' Calculate the grid coverage statistics for polygons
#'
#' @param grid_data Data frame with longitude and latitude columns
#' @param polygons sf object with polygon geometries
#' @param polygon_id_cols Column names that identify the polygons
#' @return List with coverage statistics
#' @export
check_grid_coverage <- function(grid_data, polygons, polygon_id_cols = NULL) {
  if (!requireNamespace("sf", quietly = TRUE)) {
    stop("Package 'sf' is necessary")
  }

  if (is.null(polygon_id_cols)) {
    polygon_id_cols <- setdiff(names(polygons), attr(polygons, "sf_column"))
  }

  local_s2_off()

  grid_pts <- grid_data %>% dplyr::distinct(longitude, latitude)
  pts_sf <- sf::st_as_sf(grid_pts, coords = c("longitude", "latitude"), crs = 4326)

  containment <- suppressMessages(sf::st_contains(polygons, pts_sf))
  n_points_per_polygon <- lengths(containment)

  points_per_polygon <- polygons %>%
    as.data.frame() %>%
    dplyr::select(dplyr::all_of(polygon_id_cols))
  points_per_polygon$n_points <- n_points_per_polygon

  n_with_points <- sum(n_points_per_polygon > 0)
  n_without_points <- nrow(polygons) - n_with_points

  list(
    total_polygons = nrow(polygons),
    total_grid_points = nrow(grid_pts),
    polygons_with_points = n_with_points,
    polygons_without_points = n_without_points,
    coverage_percent = round(100 * n_with_points / nrow(polygons), 1),
    points_per_polygon = points_per_polygon,
    summary = sprintf(
      "%d/%d polygons (%.1f%%) contain at least one grid point",
      n_with_points, nrow(polygons), 100 * n_with_points / nrow(polygons)
    )
  )
}
