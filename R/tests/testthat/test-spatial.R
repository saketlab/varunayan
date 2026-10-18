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
    value_col = c(value = "temperature"), method = "point_in_polygon"
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
    value_col = c(value = "temperature"), method = "point_in_polygon", agg_fun = max
  ))
  expect_equal(out$value[out$region == "west"], 74.5)
  expect_equal(out$value[out$region == "east"], 77.5)

  out_sum <- quiet(aggregate_to_polygons(g, two_regions(),
    value_col = c(value = "temperature"), method = "point_in_polygon", agg_fun = sum
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
    value_col = c(value = "temperature"), method = "point_in_polygon"
  ))
  expect_equal(nrow(out), 2)
  expect_equal(out$value[out$region == "covered"], 73.5)
  expect_true(is.na(out$value[out$region == "empty"]))
})

test_that("nearest_centroid picks the grid point closest to each centroid", {
  # Grid containing the exact centroids (73.5, 20) and (76.5, 20)
  g <- expand.grid(longitude = seq(72.5, 77.5, by = 1), latitude = seq(18, 22, by = 1))
  g$val <- g$longitude * 100 + g$latitude
  out <- quiet(aggregate_to_polygons(g, two_regions(), value_col = c(value = "val")))
  expect_named(out, c("region", "value"))
  expect_equal(out$value[out$region == "west"], 73.5 * 100 + 20)
  expect_equal(out$value[out$region == "east"], 76.5 * 100 + 20)

  # identity skips grouping and keeps polygon order
  out_id <- quiet(aggregate_to_polygons(g, two_regions(),
    value_col = c(value = "val"), agg_fun = identity
  ))
  expect_equal(out_id$region, c("west", "east"))
  expect_equal(out_id$value, c(7370, 7670))
})

test_that("aggregate_to_polygons respects polygon_id_cols and restores s2", {
  polys <- two_regions()
  polys$code <- c("W", "E")
  old <- sf::sf_use_s2()
  out <- quiet(aggregate_to_polygons(interior_grid(), polys,
    value_col = c(value = "temperature"), method = "point_in_polygon", polygon_id_cols = "code"
  ))
  expect_named(out, c("code", "value"))
  expect_equal(sf::sf_use_s2(), old)

  # default id cols = all non-geometry columns
  out2 <- quiet(aggregate_to_polygons(interior_grid(), polys,
    value_col = c(value = "temperature"), method = "point_in_polygon"
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
  expect_error(visualize_grid_overlap("grid.nc", two_regions()), "does not support NetCDF input")
})

test_that("compare_grids requires named grids", {
  skip_if_not_installed("ggplot2")
  g <- interior_grid()
  expect_error(compare_grids(g), "Give a name to each grid")
  expect_error(compare_grids(a = g, g), "Give a name to each grid")
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

skip_if_not_installed("sf")

square <- function(x0, size = 1) {
  sf::st_polygon(list(rbind(
    c(x0, 0), c(x0 + size, 0), c(x0 + size, size), c(x0, size), c(x0, 0)
  )))
}

polygons <- sf::st_sf(
  id = c("a", "b", "tiny"),
  geometry = sf::st_sfc(square(0), square(1), square(2.05, 0.1), crs = 4326)
)

grid <- expand.grid(
  longitude = c(0.25, 0.75, 1.25, 1.75, 2.25),
  latitude = 0.25,
  date = as.Date("2020-01-01") + 0:1
)
grid$temp <- seq_len(nrow(grid))
grid$rh <- 2 * grid$temp

test_that("aggregate_to_polygons keeps the single-column result for each polygon", {
  res <- aggregate_to_polygons(grid, polygons, "temp", method = "point_in_polygon")
  expect_named(res, c("id", "temp"))
  expect_equal(res$temp, c(mean(c(1, 2, 6, 7)), mean(c(3, 4, 8, 9)), NA))
})

test_that("aggregate_to_polygons aggregates several columns for each date", {
  res <- aggregate_to_polygons(grid, polygons, c("temp", "rh"),
    method = "point_in_polygon", by = "date", fill_empty = TRUE
  )
  res <- res[order(res$id, res$date), ]
  expect_named(res, c("id", "date", "temp", "rh"))
  expect_equal(res$temp, c(1.5, 6.5, 3.5, 8.5, 5, 10))
  expect_equal(res$rh, 2 * res$temp)
})

test_that("nearest_centroid uses one cell for each polygon and each date", {
  res <- aggregate_to_polygons(grid, polygons, "temp", by = "date")
  expect_equal(nrow(res), 6)
  expect_equal(res$temp[res$id == "tiny"], c(5, 10))
})

test_that("a polygon with no cell has a row with NA for each value of by", {
  res <- aggregate_to_polygons(grid, polygons, "temp", method = "point_in_polygon", by = "date")
  expect_equal(nrow(res), 6)
  expect_true(all(is.na(res$temp[res$id == "tiny"])))
})

test_that("agg_fun gets the values without extra arguments", {
  res <- aggregate_to_polygons(grid, polygons, "temp", method = "point_in_polygon", agg_fun = max)
  expect_equal(res$temp, c(7, 9, NA))
})

test_that("aggregate_to_polygons does not change a data.table input", {
  dt <- data.table::as.data.table(grid)
  before <- data.table::copy(dt)
  aggregate_to_polygons(dt, polygons, "temp", method = "point_in_polygon", by = "date")
  expect_identical(dt, before)
})

test_that("aggregate_to_polygons uses the names of value_col for the result", {
  res <- aggregate_to_polygons(grid, polygons, c(t = "temp"), method = "point_in_polygon", by = "date")
  expect_named(res, c("id", "date", "t"))
  res <- aggregate_to_polygons(grid, polygons, c(t = "temp", "rh"), method = "point_in_polygon", by = "date")
  expect_named(res, c("id", "date", "t", "rh"))
  expect_equal(res$rh, 2 * res$t)
})

test_that("aggregate_to_polygons gives no messages about s2 or planar coordinates", {
  expect_silent(aggregate_to_polygons(grid, polygons, "temp", method = "point_in_polygon", fill_empty = TRUE))
  expect_silent(aggregate_to_polygons(grid, polygons, "temp"))
})

test_that("local_s2_off switches s2 off without a message and restores it", {
  f <- function() {
    local_s2_off()
    sf::sf_use_s2()
  }
  before <- sf::sf_use_s2()
  expect_silent(inside <- f())
  expect_false(inside)
  expect_identical(sf::sf_use_s2(), before)
})

test_that("check_grid_coverage gives no messages", {
  expect_silent(cov <- check_grid_coverage(grid, polygons, "id"))
  expect_equal(cov$polygons_without_points, 1)
})
