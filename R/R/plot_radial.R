# Radial calendar and 24-hour clock plots (ggplot2). Python: plot.plot_radial*.

utils::globalVariables(c("angle", "ring", "width", "hour", "value", "x", "y", "label"))

.RADIAL_MISSING <- "#d9d9d9"
.RADIAL_HOLE <- 1.5 # empty centre, in rings, so the inner ring is not a point

# panel, t, value; zone-less times are UTC (ERA5); date and hour columns are combined
.radial_frame <- function(data, value, time, by, tz) {
  t <- lubridate::as_datetime(data[[time]], tz = "UTC")
  ok <- !is.na(t)
  if (!is.null(data$hour) && all(format(t[ok], "%H:%M:%S", tz = "UTC") == "00:00:00")) {
    t <- t + as.numeric(data$hour) * 3600
  }
  if (!is.null(tz)) t <- lubridate::with_tz(t, tz)
  panel <- if (is.null(by)) rep("", nrow(data)) else as.character(data[[by]])
  d <- data.frame(panel = panel, t = t, value = as.numeric(data[[value]]), stringsAsFactors = FALSE)
  d <- d[!is.na(d$t), , drop = FALSE]
  if (nrow(d) == 0) stop(sprintf("No dated rows in column '%s'.", time), call. = FALSE)
  d
}

.radial_fill <- function(cmap, center, values, legend) {
  limits <- NULL
  if (!is.null(center)) {
    lim <- max(abs(values - center), na.rm = TRUE)
    limits <- center + c(-lim, lim)
  }
  .fill_scale(cmap,
    limits = limits, name = legend, na.value = .RADIAL_MISSING,
    guide = ggplot2::guide_colourbar(barwidth = ggplot2::unit(15, "lines"), title.position = "top")
  )
}

.radial_theme <- function() {
  theme_varunayan() +
    ggplot2::theme(
      panel.grid.major = ggplot2::element_blank(),
      panel.grid.minor = ggplot2::element_blank(),
      axis.title = ggplot2::element_blank(),
      axis.ticks = ggplot2::element_blank(),
      axis.text.y = ggplot2::element_blank(),
      strip.text = ggplot2::element_text(face = "bold", size = ggplot2::rel(1.2)),
      legend.position = "bottom",
      plot.title = ggplot2::element_text(face = "bold", hjust = 0.5),
      plot.caption = ggplot2::element_text(hjust = 0.5, colour = "grey30")
    )
}

#' Radial calendar: one ring per year, one cell per day
#'
#' The first year is at the centre and the last at the edge. 1 January is at
#' 12 o'clock and the year runs clockwise. Days without a value are grey.
#' Works for any quantity (temperature, precipitation, a heat index, ...).
#'
#' @param data Data frame with `value` and `time` columns, such as
#'   `era5ify_*()` output. Hourly output (`date` and `hour`) is reduced to one
#'   value per day with `agg`.
#' @param value Column to colour by
#' @param time Date or date-time column
#' @param by Optional column. One circle per value (for example a district).
#' @param agg How to reduce several values in a day: `"mean"`, `"sum"`,
#'   `"max"` or `"min"`. The default sums accumulated ERA5 variables such as
#'   `tp` and averages the others.
#' @param cmap Viridis option name or a palette name from
#'   [ggplot2::scale_fill_distiller()]. For precipitation try `"Blues"`.
#' @param center Centre a diverging palette on this value (for example 0 for
#'   an anomaly)
#' @param ncol Number of panel columns when `by` is set
#' @param title Plot title
#' @param legend_title Colour bar title. The default is `value`.
#' @return ggplot object
#' @export
#' @examplesIf requireNamespace("ggplot2", quietly = TRUE)
#' days <- seq(as.Date("2022-01-01"), as.Date("2024-12-31"), "day")
#' doy <- as.numeric(format(days, "%j"))
#' df <- data.frame(date = days, t2m = 26 + 5 * sin(2 * pi * (doy - 100) / 365))
#' plot_radial(df, "t2m", legend_title = "deg C")
plot_radial <- function(data, value, time = "date", by = NULL, agg = NULL,
                        cmap = "RdYlBu", center = NULL, ncol = 2, title = NULL,
                        legend_title = NULL) {
  need_ggplot2()
  agg <- if (is.null(agg)) {
    if (is_sum_var(value)) "sum" else "mean"
  } else {
    match.arg(agg, c("mean", "sum", "max", "min"))
  }
  d <- .radial_frame(data, value, time, by, NULL)
  d$day <- as.Date(d$t, tz = "UTC")
  fn <- match.fun(agg)
  key <- paste(d$panel, d$day)
  # an all-missing day stays missing (not 0 or -Inf)
  daily <- tapply(d$value, key, function(x) if (all(is.na(x))) NA_real_ else fn(x, na.rm = TRUE))

  # full calendar, so missing days show grey
  years <- as.integer(format(range(d$day), "%Y"))
  days <- seq(as.Date(sprintf("%d-01-01", years[1])), as.Date(sprintf("%d-12-31", years[2])), "day")
  cal <- expand.grid(day = days, panel = sort(unique(d$panel)), stringsAsFactors = FALSE)
  cal$value <- as.numeric(daily[paste(cal$panel, cal$day)])

  # angle in months; leap years also span 0-12
  lt <- as.POSIXlt(cal$day)
  year <- lt$year + 1900L
  leap <- (year %% 4 == 0 & year %% 100 != 0) | year %% 400 == 0
  cal$width <- 12 / (365 + leap)
  cal$angle <- (lt$yday + 0.5) * cal$width
  cal$ring <- year - years[1] + 1 + .RADIAL_HOLE

  span <- if (years[2] > years[1]) {
    sprintf("%d at the centre, %d at the edge", years[1], years[2])
  } else {
    years[1]
  }
  p <- ggplot2::ggplot(cal, ggplot2::aes(angle, ring, fill = value)) +
    ggplot2::geom_tile(ggplot2::aes(width = width), height = 0.9) +
    .radial_fill(cmap, center, cal$value, legend_title %||% value) +
    ggplot2::scale_x_continuous(
      limits = c(0, 12), breaks = 0:11 + 0.5, labels = month.abb, expand = c(0, 0)
    ) +
    ggplot2::scale_y_continuous(limits = c(0, max(cal$ring) + 0.5), expand = c(0, 0)) +
    ggplot2::coord_polar(start = 0, clip = "off") +
    ggplot2::labs(title = title, caption = sprintf("One ring per year: %s. Grey: no data.", span)) +
    .radial_theme()
  if (!is.null(by)) p <- p + ggplot2::facet_wrap(~panel, ncol = ncol)
  p
}

#' 24-hour clock: the angle is the hour of the day
#'
#' Midnight is at 12 o'clock and noon at 6 o'clock, so the day runs clockwise
#' like a clock face. With `rings = "month"` each ring is a calendar month
#' (January at the centre, December at the edge) and each cell is the mean for
#' that hour over all days of that month in all years: the daily cycle and how
#' it changes with the seasons. With `rings = "day"` each ring is one date.
#'
#' @inheritParams plot_radial
#' @param data Hourly data frame with `value` and `time` columns, such as
#'   `era5ify_*(frequency = "hourly")` output (`date` and `hour` columns are
#'   combined).
#' @param by Optional column. One clock per value.
#' @param rings `"month"` or `"day"`
#' @param accumulated Each value is the total of the hour that ends at its
#'   time, as ERA5 precipitation; otherwise a reading centred in its cell.
#'   The default is `TRUE` for accumulated ERA5 variables (`tp`).
#' @param tz Time zone for the hour of day, such as `"Asia/Kolkata"`. Times
#'   without a time zone are taken as UTC, as in ERA5. The default draws UTC
#'   hours.
#' @return ggplot object
#' @export
#' @examplesIf requireNamespace("ggplot2", quietly = TRUE)
#' t <- seq(as.POSIXct("2023-01-01", tz = "UTC"), by = "hour", length.out = 24 * 365)
#' doy <- as.numeric(format(t, "%j"))
#' hr <- as.numeric(format(t, "%H"))
#' df <- data.frame(time = t, t2m = 26 + 5 * sin(2 * pi * (doy - 100) / 365) +
#'   4 * sin(2 * pi * (hr - 3.5) / 24))
#' plot_radial_hourly(df, "t2m", time = "time", tz = "Asia/Kolkata")
plot_radial_hourly <- function(data, value, time = "date", by = NULL, rings = c("month", "day"),
                               tz = NULL, accumulated = NULL, cmap = "RdYlBu", center = NULL,
                               ncol = 2, title = NULL, legend_title = NULL) {
  need_ggplot2()
  rings <- match.arg(rings)
  d <- .radial_frame(data, value, time, by, tz)
  zone <- tz %||% "UTC"
  if (is.null(accumulated)) accumulated <- is_sum_var(value)
  # a cell starts 30 min before a reading, or 60 min before an hourly total
  start <- d$t - if (accumulated) 3600 else 1800
  lt <- as.POSIXlt(start, tz = zone)
  if (length(unique(lt$min)) == 1) {
    offset <- lt$min[1] / 60 # cells start this far past the hour
  } else { # mixed minutes, such as 15-minute data: whole clock hours
    lt <- as.POSIXlt(start + 1800, tz = zone)
    lt <- as.POSIXlt(start + 1800 - (lt$min * 60 + lt$sec), tz = zone)
    offset <- 0
  }
  d$hour <- lt$hour
  if (rings == "month") {
    d$key <- lt$mon + 1L
    keys <- 1:12
    starts <- 1:12
    labels <- month.abb
    what <- "One ring per month (January at the centre): mean of each hour"
  } else {
    d$key <- as.Date(lt)
    keys <- seq(min(d$key), max(d$key), "day")
    yearly <- length(keys) > 366 # one label per year, not per month
    starts <- which(format(keys, "%d") == "01" & (!yearly | format(keys, "%m") == "01"))
    if (length(starts) == 0) starts <- 1
    labels <- format(keys[starts], if (yearly) "%Y" else "%b")
    what <- "One ring per day, first day at the centre"
  }
  cells <- tapply(d$value, paste(d$panel, d$key, d$hour), mean, na.rm = TRUE)
  cells[is.nan(cells)] <- NA

  grid <- expand.grid(hour = 0:23, k = seq_along(keys), panel = sort(unique(d$panel)), stringsAsFactors = FALSE)
  grid$value <- as.numeric(cells[paste(grid$panel, keys[grid$k], grid$hour)])
  grid$ring <- grid$k - 0.5 + .RADIAL_HOLE
  breaks <- starts - 0.5 + .RADIAL_HOLE
  top <- length(keys) + .RADIAL_HOLE
  # the x scale runs from offset to offset + 24; midnight is 24 when cells start past 00:00
  midnight <- if (offset > 0) 24 else 0
  hours <- c(midnight, seq(3, 21, 3))
  grid$x <- grid$hour + 0.5 + offset
  p <- ggplot2::ggplot(grid, ggplot2::aes(x, ring, fill = value)) +
    ggplot2::geom_tile(width = 1, height = 1) +
    # quarter-day spokes help read the hour
    # data layers repeat in every facet; annotate() fails with facets
    ggplot2::geom_segment(
      data = data.frame(x = c(midnight, 6, 12, 18)),
      ggplot2::aes(x = x, xend = x, y = .RADIAL_HOLE, yend = top), inherit.aes = FALSE,
      colour = "white", linewidth = 0.3, alpha = 0.7
    ) +
    # ring labels on the midnight spoke; coord_polar draws no radial axis text
    ggplot2::geom_text(
      data = data.frame(y = breaks, label = labels),
      ggplot2::aes(x = midnight + 0.1, y = y, label = label), inherit.aes = FALSE,
      size = 2.6, hjust = 0, colour = "grey15"
    ) +
    .radial_fill(cmap, center, grid$value, legend_title %||% value) +
    ggplot2::scale_x_continuous(
      limits = c(offset, offset + 24), breaks = hours, labels = sprintf("%02d:00", hours %% 24),
      expand = c(0, 0)
    ) +
    ggplot2::scale_y_continuous(limits = c(0, top), expand = c(0, 0)) +
    ggplot2::coord_polar(start = offset * pi / 12, clip = "off") +
    ggplot2::labs(
      title = title,
      caption = sprintf("Hour of day (%s) clockwise from midnight at the top.\n%s. Grey: no data.", zone, what)
    ) +
    .radial_theme()
  if (!is.null(by)) p <- p + ggplot2::facet_wrap(~panel, ncol = ncol)
  p
}
