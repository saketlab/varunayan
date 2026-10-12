# Tests for grid-to-polygon utilities (R/spatial.R). All data are synthetic.

# sf emits informational s2/planar messages and centroid warnings; silence them.
quiet <- function(expr) suppressMessages(suppressWarnings(expr))

make_box <- function(xmin, ymin, xmax, ymax) {
  sf::st_polygon(list(rbind(
    c(xmin, ymin), c(xmax, ymin), c(xmax, ymax), c(xmin, ymax), c(xmin, ymin)
  )))
}

two_regions <- function() {
  sf::st_sf(
    region = c("west", "east"),
    geometry = sf::st_sfc(make_box(72, 18, 75, 22), make_box(75, 18, 78, 22), crs = 4326)
  )
}

# Interior grid: lon 72.5..77.5, lat 18.5..21.5, value encodes position.
interior_grid <- function() {
  g <- expand.grid(longitude = seq(72.5, 77.5, by = 1), latitude = seq(18.5, 21.5, by = 1))
  g$temperature <- g$longitude
  g
}

test_that("point_in_polygon aggregates the points inside each polygon", {
  out <- quiet(aggregate_to_polygons(interior_grid(), two_regions(),
    value_col = "temperature", method = "point_in_polygon"
  ))
  expect_s3_class(out, "data.frame")
  expect_named(out, c("region", "value"))
  out <- out[order(out$region), ]
  # west contains lon 72.5, 73.5, 74.5 -> mean 73.5; east 75.5..77.5 -> 76.5
  expect_equal(out$value[out$region == "west"], 73.5)
  expect_equal(out$value[out$region == "east"], 76.5)
})

test_that("point_in_polygon honours a custom aggregation function", {
  g <- interior_grid()
  out <- quiet(aggregate_to_polygons(g, two_regions(),
    value_col = "temperature", method = "point_in_polygon", agg_fun = max
  ))
  expect_equal(out$value[out$region == "west"], 74.5)
  expect_equal(out$value[out$region == "east"], 77.5)

  out_sum <- quiet(aggregate_to_polygons(g, two_regions(),
    value_col = "temperature", method = "point_in_polygon", agg_fun = sum
  ))
  # 4 latitudes per longitude
  expect_equal(out_sum$value[out_sum$region == "west"], 4 * (72.5 + 73.5 + 74.5))
})

test_that("point_in_polygon yields NA-safe result for empty polygons", {
  polys <- sf::st_sf(
    region = c("covered", "empty"),
    geometry = sf::st_sfc(make_box(72, 18, 75, 22), make_box(90, 0, 91, 1), crs = 4326)
  )
  out <- quiet(aggregate_to_polygons(interior_grid(), polys,
    value_col = "temperature", method = "point_in_polygon"
  ))
  expect_equal(nrow(out), 2)
  expect_equal(out$value[out$region == "covered"], 73.5)
  expect_true(is.nan(out$value[out$region == "empty"]))
})

test_that("nearest_centroid picks the grid point closest to each centroid", {
  # Grid containing the exact centroids (73.5, 20) and (76.5, 20)
  g <- expand.grid(longitude = seq(72.5, 77.5, by = 1), latitude = seq(18, 22, by = 1))
  g$val <- g$longitude * 100 + g$latitude
  out <- quiet(aggregate_to_polygons(g, two_regions(), value_col = "val"))
  expect_named(out, c("region", "value"))
  expect_equal(out$value[out$region == "west"], 73.5 * 100 + 20)
  expect_equal(out$value[out$region == "east"], 76.5 * 100 + 20)

  # identity skips grouping and keeps polygon order
  out_id <- quiet(aggregate_to_polygons(g, two_regions(),
    value_col = "val", agg_fun = identity
  ))
  expect_equal(out_id$region, c("west", "east"))
  expect_equal(out_id$value, c(7370, 7670))
})

test_that("aggregate_to_polygons respects polygon_id_cols and restores s2", {
  polys <- two_regions()
  polys$code <- c("W", "E")
  old <- sf::sf_use_s2()
  out <- quiet(aggregate_to_polygons(interior_grid(), polys,
    value_col = "temperature", method = "point_in_polygon", polygon_id_cols = "code"
  ))
  expect_named(out, c("code", "value"))
  expect_equal(sf::sf_use_s2(), old)

  # default id cols = all non-geometry columns
  out2 <- quiet(aggregate_to_polygons(interior_grid(), polys,
    value_col = "temperature", method = "point_in_polygon"
  ))
  expect_named(out2, c("region", "code", "value"))
})

test_that("aggregate_to_polygons rejects unknown methods", {
  expect_error(
    aggregate_to_polygons(interior_grid(), two_regions(), "temperature", method = "kriging"),
    "should be one of"
  )
})

test_that("check_grid_coverage counts points per polygon", {
  polys <- sf::st_sf(
    region = c("west", "east", "ocean"),
    geometry = sf::st_sfc(
      make_box(72, 18, 75, 22), make_box(75, 18, 78, 22), make_box(60, 0, 61, 1),
      crs = 4326
    )
  )
  g <- interior_grid()
  g <- rbind(g, g) # duplicates must be collapsed
  old <- sf::sf_use_s2()
  cov <- quiet(check_grid_coverage(g, polys))
  expect_equal(sf::sf_use_s2(), old)
  expect_equal(cov$total_polygons, 3)
  expect_equal(cov$total_grid_points, 24)
  expect_equal(cov$polygons_with_points, 2)
  expect_equal(cov$polygons_without_points, 1)
  expect_equal(cov$coverage_percent, 66.7)
  expect_equal(cov$points_per_polygon$region, c("west", "east", "ocean"))
  expect_equal(cov$points_per_polygon$n_points, c(12L, 12L, 0L))
  expect_equal(cov$summary, "2/3 polygons (66.7%) contain at least one grid point")
})

test_that("check_grid_coverage honours explicit polygon_id_cols", {
  polys <- two_regions()
  polys$code <- c("W", "E")
  cov <- quiet(check_grid_coverage(interior_grid(), polys, polygon_id_cols = "code"))
  expect_named(cov$points_per_polygon, c("code", "n_points"))
  expect_equal(cov$coverage_percent, 100)
})

test_that("visualize_grid_overlap builds a ggplot from data frames and files", {
  skip_if_not_installed("ggplot2")
  polys <- two_regions()
  g <- interior_grid()
  p <- quiet(visualize_grid_overlap(g, polys))
  expect_s3_class(p, "ggplot")
  expect_equal(p$labels$title, "Grid-Polygon Overlap")
  expect_equal(p$labels$subtitle, "Grid points: 24 | Polygons: 2")
  expect_length(p$layers, 3)

  p2 <- visualize_grid_overlap(g, polys, show_centroids = FALSE, title = "T")
  expect_length(p2$layers, 2)
  expect_equal(p2$labels$title, "T")

  csv <- tempfile(fileext = ".csv")
  gj <- tempfile(fileext = ".geojson")
  on.exit(unlink(c(csv, gj)), add = TRUE)
  utils::write.csv(g, csv, row.names = FALSE)
  sf::st_write(polys, gj, quiet = TRUE)
  p3 <- visualize_grid_overlap(csv, gj, show_centroids = FALSE)
  expect_equal(p3$labels$subtitle, "Grid points: 24 | Polygons: 2")
})

test_that("visualize_grid_overlap rejects NetCDF paths", {
  skip_if_not_installed("ggplot2")
  expect_error(visualize_grid_overlap("grid.nc", two_regions()), "NetCDF input not yet supported")
})

test_that("compare_grids requires named grids", {
  skip_if_not_installed("ggplot2")
  g <- interior_grid()
  expect_error(compare_grids(g), "must be named")
  expect_error(compare_grids(a = g, g), "must be named")
})

test_that("compare_grids plots each grid with counts in the subtitle", {
  skip_if_not_installed("ggplot2")
  g <- interior_grid()
  coarse <- g[g$longitude < 75, ]
  p <- compare_grids(fine = g, coarse = coarse)
  expect_s3_class(p, "ggplot")
  expect_equal(p$labels$subtitle, "fine: 24 pts | coarse: 12 pts")
  expect_equal(p$coordinates$ratio, 1)
  built <- ggplot2::ggplot_build(p)
  expect_equal(nrow(built$data[[1]]), 36)

  gj <- tempfile(fileext = ".geojson")
  on.exit(unlink(gj), add = TRUE)
  sf::st_write(two_regions(), gj, quiet = TRUE)
  p2 <- compare_grids(
    A = g, B = coarse, polygons = gj,
    colors = c(A = "red", B = "blue"), shapes = c(A = 1, B = 2), title = "Cmp"
  )
  expect_equal(p2$labels$title, "Cmp")
  expect_s3_class(p2$coordinates, "CoordSf")
  expect_length(p2$layers, 2)
})
