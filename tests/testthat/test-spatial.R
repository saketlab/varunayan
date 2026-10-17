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
