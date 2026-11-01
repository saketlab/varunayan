hourly <- function() {
  # era5ify_*(frequency = "hourly") shape: date + hour (UTC)
  data.frame(
    date = c(rep("2023-01-01", 3), "2024-12-31"), hour = c(0, 1, 2, 23),
    tp = c(1, 2, 3, 4)
  )
}

test_that("plot_radial puts each day on its year ring and applies agg per day", {
  skip_if_not_installed("ggplot2")
  p <- plot_radial(hourly(), "tp", title = "Rain") # tp is summed by default
  d <- p$data
  expect_equal(nrow(d), 365 + 366) # full calendar, gaps included
  expect_equal(d$value[d$day == as.Date("2023-01-01")], 6)
  expect_true(is.na(d$value[d$day == as.Date("2023-01-02")]))
  expect_equal(d$value[d$day == as.Date("2024-12-31")], 4)
  expect_lt(d$ring[1], d$ring[nrow(d)])
  expect_identical(ggplot2::get_labs(p)$title, "Rain")
  expect_s3_class(ggplot2::ggplot_build(p), "ggplot_built")
})

test_that("plot_radial centres the palette and facets by group", {
  skip_if_not_installed("ggplot2")
  df <- data.frame(date = "2024-03-01", city = c("B", "A"), anom = c(-1, 3))
  p <- plot_radial(df, "anom", by = "city", center = 0)
  b <- ggplot2::ggplot_build(p)
  expect_equal(length(unique(b$layout$layout$PANEL)), 2)
  expect_equal(b$plot$scales$get_scales("fill")$get_limits(), c(-3, 3))
})

test_that("plot_radial_hourly bins local hours into month rings", {
  skip_if_not_installed("ggplot2")
  d <- plot_radial_hourly(hourly(), "tp", tz = "Asia/Kolkata", accumulated = FALSE)$data
  cell <- function(k, h) d$value[d$k == k & d$hour == h]
  # 00:00 UTC on 1 Jan is 05:30 IST: January ring, hour 5
  expect_equal(cell(1, 5), 1)
  expect_equal(cell(1, 7), 3)
  # 23:00 UTC on 31 Dec 2024 is 04:30 IST on 1 Jan 2025
  expect_equal(cell(1, 4), 4)
  expect_true(all(is.na(d$value[d$k == 12])))
})

test_that("plot_radial_hourly centres each reading in its cell", {
  skip_if_not_installed("ggplot2")
  d <- plot_radial_hourly(hourly(), "tp", rings = "day", accumulated = FALSE)$data
  # 00:00 on 1 Jan fills 23:30-00:30, so the first ring is 31 Dec 2022
  n_days <- as.integer(as.Date("2024-12-31") - as.Date("2022-12-31")) + 1
  expect_equal(max(d$k), n_days)
  expect_equal(d$value[d$k == 1 & d$hour == 23], 1)
  expect_equal(d$value[d$k == 2 & d$hour == 0], 2)
  expect_equal(d$x[d$k == 2 & d$hour == 0], 1) # cell 00:30-01:30, centre 01:00
  expect_error(plot_radial_hourly(hourly(), "tp", rings = "week"))
})

test_that("plot_radial_hourly with accumulated fills the hour before", {
  skip_if_not_installed("ggplot2")
  # rain stamped 12:00 UTC fell 11:00-12:00 UTC, 16:30-17:30 IST
  rain <- data.frame(time = as.POSIXct("2023-07-01 12:00", tz = "UTC"), tp = 5)
  p <- plot_radial_hourly(rain, "tp", time = "time", tz = "Asia/Kolkata") # tp: accumulated
  d <- p$data
  expect_equal(d$value[d$k == 7 & d$hour == 16], 5)
  expect_equal(sum(!is.na(d$value)), 1)
  expect_equal(d$x[d$k == 7 & d$hour == 16], 17) # centre of 16:30-17:30
  expect_s3_class(ggplot2::ggplot_build(p), "ggplot_built")
})

test_that("plot_radial_hourly with by draws ring labels in every panel", {
  skip_if_not_installed("ggplot2")
  df <- transform(rbind(hourly(), hourly()), city = rep(c("A", "B"), each = 4))
  b <- ggplot2::ggplot_build(plot_radial_hourly(df, "tp", by = "city"))
  expect_equal(length(unique(b$layout$layout$PANEL)), 2)
  expect_equal(nrow(b$data[[3]]), 2 * 12)
})

test_that("sequential palettes are darkest at the highest value, as in Python", {
  skip_if_not_installed("ggplot2")
  df <- data.frame(date = c("2024-03-01", "2024-03-02"), rain = c(0, 10))
  p <- plot_radial(df, "rain", cmap = "Blues")
  fill <- ggplot2::ggplot_build(p)$data[[1]]$fill # rows in the order of p$data
  dry <- fill[which(p$data$value == 0)]
  wet <- fill[which(p$data$value == 10)]
  lum <- function(hex) sum(grDevices::col2rgb(hex))
  expect_gt(lum(dry), lum(wet))
})
