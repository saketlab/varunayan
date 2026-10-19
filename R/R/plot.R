#' Plots used by the vignettes
#'
#' Each function returns a ggplot object. The Python package has the same
#' functions (matplotlib) with the same arguments.
#'
#' @name plot
#' @noRd
NULL

utils::globalVariables(c(".fill", "longitude", "latitude", "lag", "r"))

.MONTH_COLORS <- c(
  "#e6194b", "#f58231", "#ffe119", "#bfef45", "#3cb44b", "#42d4f4",
  "#4363d8", "#0000ff", "#911eb4", "#f032e6", "#fabed4", "#a40000"
)
.PALETTE <- c("#B2182B", "#2166AC", "#1B7837", "#E08214", "#762A83", "#4D4D4D")

need_ggplot2 <- function() {
  if (!requireNamespace("ggplot2", quietly = TRUE)) {
    stop("Package 'ggplot2' is necessary for plots: install.packages('ggplot2')")
  }
}

theme_varunayan <- function() {
  ggplot2::theme_minimal(base_size = 11) +
    ggplot2::theme(panel.grid.minor = ggplot2::element_blank())
}

#' Map one or more columns of gridded or polygon data
#'
#' An sf object with polygons gives a choropleth. A data frame with
#' `latitude` and `longitude` gives one square for each grid point.
#'
#' @param data sf object with polygons, or data frame with latitude and longitude
#' @param column Column to colour by. A vector gives one panel per column,
#'   with one shared colour scale.
#' @param boundaries Optional sf polygons to draw as outlines on top
#' @param facet Optional column. One panel per value (for example a period).
#' @param log Use a log colour scale (values must be positive)
#' @param months The values are months (1-12). Use 12 discrete colours and
#'   month names in the legend, for example for `peak_month`.
#' @param labels Optional column to write at each polygon centre
#' @param cmap Viridis option name (`"viridis"`, `"plasma"`, ...) or a
#'   diverging palette name from [ggplot2::scale_fill_distiller()]
#' @param center Centre a diverging palette on this value, with limits the
#'   same distance on each side (for example 0 for a bias). Use it with a
#'   diverging `cmap` such as `"RdBu"`.
#' @param title Plot title
#' @param legend_title Legend title. The default is the column name.
#' @return ggplot object
#' @export
#' @examplesIf requireNamespace("ggplot2", quietly = TRUE)
#' grid <- expand.grid(latitude = seq(10, 12, 0.5), longitude = seq(70, 72, 0.5))
#' grid$t2m <- grid$latitude + grid$longitude
#' plot_map(grid, "t2m")
plot_map <- function(data, column, boundaries = NULL, facet = NULL, log = FALSE,
                     months = FALSE, labels = NULL, cmap = "viridis", center = NULL,
                     title = NULL, legend_title = NULL) {
  need_ggplot2()
  is_sf <- inherits(data, "sf")
  is_polygon <- is_sf && !all(sf::st_geometry_type(data) %in% c("POINT", "MULTIPOINT"))
  if (length(column) > 1) {
    # One panel per column: stack the columns into one "value" column.
    keep <- if (is_sf) attr(data, "sf_column") else c("latitude", "longitude")
    parts <- lapply(column, function(col) {
      part <- data[c(keep, col, labels)]
      names(part)[names(part) == col] <- ".value"
      part$.panel <- factor(col, levels = column)
      part
    })
    data <- do.call(rbind, parts)
    fill_col <- ".value"
    facet <- ".panel"
  } else {
    fill_col <- column
  }
  data$.fill <- if (months) factor(data[[fill_col]], levels = 1:12) else data[[fill_col]]
  p <- ggplot2::ggplot(data)
  if (is_polygon) {
    p <- p + ggplot2::geom_sf(ggplot2::aes(fill = .fill), colour = "white", linewidth = 0.1)
  } else {
    p <- p + ggplot2::geom_tile(ggplot2::aes(x = longitude, y = latitude, fill = .fill))
  }
  if (!is.null(labels) && is_polygon) {
    p <- p + ggplot2::geom_sf_text(ggplot2::aes(label = .data[[labels]]), size = 2)
  }
  if (!is.null(boundaries)) {
    p <- p + ggplot2::geom_sf(
      data = boundaries, fill = NA, colour = "black", linewidth = 0.2,
      inherit.aes = FALSE
    )
  }
  legend <- legend_title %||% column[[1]]
  if (months) {
    p <- p + ggplot2::scale_fill_manual(
      values = stats::setNames(.MONTH_COLORS, 1:12),
      labels = month.abb, drop = FALSE, name = legend
    )
  } else if (!is.null(center)) {
    lim <- max(abs(data$.fill - center), na.rm = TRUE)
    p <- p + ggplot2::scale_fill_distiller(
      palette = cmap, limits = center + c(-lim, lim),
      name = legend, na.value = "lightgrey"
    )
  } else if (cmap %in% c("viridis", "plasma", "magma", "inferno", "cividis")) {
    p <- p + ggplot2::scale_fill_viridis_c(
      option = cmap, trans = if (log) "log10" else "identity",
      name = legend, na.value = "lightgrey"
    )
  } else {
    p <- p + ggplot2::scale_fill_distiller(
      palette = cmap, trans = if (log) "log10" else "identity",
      name = legend, na.value = "lightgrey"
    )
  }
  if (!is.null(facet)) p <- p + ggplot2::facet_wrap(ggplot2::vars(.data[[facet]]))
  p <- p + if (is_polygon || !is.null(boundaries)) ggplot2::coord_sf() else ggplot2::coord_equal()
  p + ggplot2::labs(title = title, x = NULL, y = NULL) + theme_varunayan()
}

#' Line plot, one line per group
#'
#' When `x` is `"month"`, the axis shows month names.
#'
#' @param data Long data frame
#' @param x Column for the horizontal axis (for example `date` or `year`)
#' @param y Column for the vertical axis
#' @param by Optional column. One line (and colour) per value.
#' @param facet Optional column. One panel per value.
#' @param smooth `"lowess"` or `"linear"` adds a trend line. The data line is
#'   then light grey when there is no `by` column.
#' @param span Fraction of the points in each LOWESS window ([stats::lowess()] `f`)
#' @param ribbon Optional `c(low, high)` columns to shade, for example
#'   `c("temperature_min", "temperature_max")`
#' @param title Plot title
#' @param ylabel Vertical axis label. The default is `y`.
#' @return ggplot object
#' @export
#' @examplesIf requireNamespace("ggplot2", quietly = TRUE)
#' df <- data.frame(year = 2001:2020, t2m = 25 + 0.03 * (1:20) + rnorm(20, sd = 0.2))
#' plot_series(df, "year", "t2m", smooth = "linear")
plot_series <- function(data, x, y, by = NULL, facet = NULL, smooth = NULL, span = 2 / 3,
                        ribbon = NULL, title = NULL, ylabel = NULL) {
  need_ggplot2()
  data <- data[order(data[[x]]), , drop = FALSE]
  group <- if (is.null(by)) {
    NULL
  } else {
    ggplot2::aes(
      colour = factor(.data[[by]]),
      fill = factor(.data[[by]]),
      group = factor(.data[[by]])
    )
  }
  p <- ggplot2::ggplot(data, ggplot2::aes(x = .data[[x]], y = .data[[y]])) + group
  if (!is.null(ribbon)) {
    p <- p + ggplot2::geom_ribbon(ggplot2::aes(ymin = .data[[ribbon[[1]]]], ymax = .data[[ribbon[[2]]]]),
      alpha = 0.15, colour = NA
    )
  }
  line_colour <- if (!is.null(smooth) && is.null(by)) "#BDBDBD" else if (is.null(by)) .PALETTE[[1]] else NULL
  line_args <- list(linewidth = 0.5)
  if (!is.null(line_colour)) line_args$colour <- line_colour
  p <- p + do.call(ggplot2::geom_line, line_args)
  n_lines <- if (is.null(by)) 1 else length(unique(data[[by]]))
  if (nrow(data) / n_lines <= 40) {
    point_args <- list(size = 1)
    if (!is.null(line_colour)) point_args$colour <- line_colour
    p <- p + do.call(ggplot2::geom_point, point_args)
  }
  if (!is.null(smooth)) {
    trend <- smooth_by(data, x, y, by, facet, smooth, span)
    trend_args <- list(
      data = trend, linewidth = 0.9,
      linetype = if (smooth == "linear") "dashed" else "solid"
    )
    if (is.null(by)) trend_args$colour <- .PALETTE[[1]]
    p <- p + do.call(ggplot2::geom_line, trend_args)
  }
  if (!is.null(by)) {
    n <- length(unique(data[[by]]))
    values <- if (n <= length(.PALETTE)) .PALETTE[seq_len(n)] else grDevices::hcl.colors(n, "Dark 3")
    p <- p + ggplot2::scale_colour_manual(values = values, name = NULL) +
      ggplot2::scale_fill_manual(values = values, name = NULL)
  }
  if (x == "month") {
    p <- p + ggplot2::scale_x_continuous(breaks = 1:12, labels = month.abb)
  } else if (is.numeric(data[[x]]) && all(data[[x]] == round(data[[x]]), na.rm = TRUE)) {
    # Whole-number x (years): no ticks such as 2002.5.
    p <- p + ggplot2::scale_x_continuous(breaks = function(l) unique(round(pretty(l))))
  }
  if (!is.null(facet)) p <- p + ggplot2::facet_wrap(ggplot2::vars(.data[[facet]]), ncol = 1)
  p + ggplot2::labs(
    title = title, x = if (x %in% c("date", "month", "year")) NULL else x,
    y = ylabel %||% y
  ) + theme_varunayan()
}

# Trend line for each group, with stats::lowess or a linear fit.
smooth_by <- function(data, x, y, by, facet, smooth, span) {
  keys <- c(by, facet)
  split_data <- if (length(keys)) split(data, data[keys], drop = TRUE) else list(data)
  out <- lapply(split_data, function(d) {
    xs <- as.numeric(d[[x]])
    d[[y]] <- if (smooth == "linear") {
      stats::fitted(stats::lm(d[[y]] ~ xs))
    } else if (smooth == "lowess") {
      stats::lowess(xs, d[[y]], f = span)$y
    } else {
      stop("smooth must be 'lowess', 'linear' or NULL")
    }
    d
  })
  do.call(rbind, out)
}

#' Two series on a left and a right axis
#'
#' @param data Data frame with the three columns
#' @param x Column for the horizontal axis, for example `date`
#' @param left Column for the left axis
#' @param right Column for the right axis
#' @param log_right Show `log(1 + right)` on the right axis
#' @param title Plot title
#' @return ggplot object
#' @export
#' @examplesIf requireNamespace("ggplot2", quietly = TRUE)
#' df <- data.frame(month = 1:24, rain = abs(sin(1:24 / 2)) * 300, searches = abs(sin(1:24 / 2)) * 80)
#' plot_dual_axis(df, "month", "rain", "searches")
plot_dual_axis <- function(data, x, left, right, log_right = FALSE, title = NULL) {
  need_ggplot2()
  rv <- if (log_right) log1p(data[[right]]) else data[[right]]
  # Map the right series onto the range of the left series.
  lr <- range(data[[left]], na.rm = TRUE)
  rr <- range(rv, na.rm = TRUE)
  scale <- diff(lr) / diff(rr)
  data$.right <- (rv - rr[[1]]) * scale + lr[[1]]
  ggplot2::ggplot(data, ggplot2::aes(x = .data[[x]])) +
    ggplot2::geom_line(ggplot2::aes(y = .data[[left]]), colour = .PALETTE[[2]]) +
    ggplot2::geom_line(ggplot2::aes(y = .data$.right), colour = .PALETTE[[1]]) +
    ggplot2::scale_y_continuous(
      name = left,
      sec.axis = ggplot2::sec_axis(~ (. - lr[[1]]) / scale + rr[[1]],
        name = if (log_right) sprintf("log(1 + %s)", right) else right
      )
    ) +
    ggplot2::labs(title = title, x = NULL) +
    theme_varunayan() +
    ggplot2::theme(
      axis.title.y.left = ggplot2::element_text(colour = .PALETTE[[2]]),
      axis.title.y.right = ggplot2::element_text(colour = .PALETTE[[1]])
    )
}

#' Stem plot of a cross-correlation
#'
#' @param ccf Data frame with `lag` and `r`, from [cross_correlation()]
#' @param title Plot title
#' @return ggplot object
#' @export
#' @examplesIf requireNamespace("ggplot2", quietly = TRUE)
#' plot_ccf(cross_correlation(sin(1:48 / 2), cos(1:48 / 2), max_lag = 6))
plot_ccf <- function(ccf, title = NULL) {
  need_ggplot2()
  best <- ccf[which.max(abs(ccf$r)), ]
  ggplot2::ggplot(ccf, ggplot2::aes(x = lag, y = r)) +
    ggplot2::geom_hline(yintercept = 0, colour = "grey") +
    ggplot2::geom_vline(xintercept = 0, colour = "grey", linetype = "dashed") +
    ggplot2::geom_segment(ggplot2::aes(xend = lag, yend = 0), colour = .PALETTE[[2]]) +
    ggplot2::geom_point(colour = .PALETTE[[2]]) +
    ggplot2::labs(
      title = title,
      subtitle = sprintf("Largest |r| = %.2f at lag %d", best$r, as.integer(best$lag)),
      x = "Lag", y = "Cross-correlation"
    ) +
    theme_varunayan()
}

#' Scatter plot with the 1:1 line, r and bias
#'
#' @param data Data frame with the two columns
#' @param x Column for the horizontal axis (the reference)
#' @param y Column for the vertical axis
#' @param title Plot title
#' @return ggplot object
#' @export
#' @examplesIf requireNamespace("ggplot2", quietly = TRUE)
#' df <- data.frame(cru = 1:20, era5 = 1:20 + rnorm(20))
#' plot_scatter(df, "cru", "era5")
plot_scatter <- function(data, x, y, title = NULL) {
  need_ggplot2()
  d <- data[!is.na(data[[x]]) & !is.na(data[[y]]), , drop = FALSE]
  s <- compare(d, x, y)
  ggplot2::ggplot(d, ggplot2::aes(x = .data[[x]], y = .data[[y]])) +
    ggplot2::geom_abline(slope = 1, intercept = 0, colour = "grey", linetype = "dashed") +
    ggplot2::geom_point(size = 1, alpha = 0.6, colour = "#34495E") +
    ggplot2::coord_equal() +
    ggplot2::labs(
      title = title,
      subtitle = sprintf("r = %.3f, bias (%s - %s) = %+.2f, n = %d", s$r, y, x, s$bias, s$n),
      x = x, y = y
    ) +
    theme_varunayan()
}

#' Bar chart coloured by value
#'
#' @param data Data frame with the two columns
#' @param x Category column (for example `state_name` or `year`)
#' @param y Value column
#' @param horizontal Draw horizontal bars (for long category names)
#' @param sort Sort the bars by value, largest first
#' @param cmap Diverging palette name from [ggplot2::scale_fill_distiller()].
#'   The scale is centred on zero when there are negative values.
#' @param title Plot title
#' @return ggplot object
#' @export
#' @examplesIf requireNamespace("ggplot2", quietly = TRUE)
#' df <- data.frame(year = 2001:2010, dev = seq(-1, 1, length.out = 10))
#' plot_bars(df, "year", "dev")
plot_bars <- function(data, x, y, horizontal = FALSE, sort = FALSE, cmap = "RdBu", title = NULL) {
  need_ggplot2()
  d <- data[!is.na(data[[y]]), , drop = FALSE]
  lev <- if (sort) d[[x]][order(d[[y]], decreasing = !horizontal)] else unique(d[[x]])
  d[[x]] <- factor(d[[x]], levels = unique(lev))
  lim <- if (min(d[[y]]) < 0) c(-1, 1) * max(abs(d[[y]])) else range(d[[y]])
  p <- ggplot2::ggplot(d, ggplot2::aes(x = .data[[x]], y = .data[[y]], fill = .data[[y]])) +
    ggplot2::geom_col() +
    ggplot2::scale_fill_distiller(palette = cmap, limits = lim, guide = "none") +
    ggplot2::labs(title = title, x = NULL, y = y) +
    theme_varunayan()
  if (horizontal) {
    p <- p + ggplot2::coord_flip()
  } else {
    p <- p + ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 90, vjust = 0.5))
  }
  p
}

#' Heat map of a matrix or of a long data frame
#'
#' @param data Long data frame (with `x`, `y` and `value`), or a matrix /
#'   wide data frame such as `cor(df)` (then leave `x`, `y` and `value` empty)
#' @param x Column for the columns of the heat map (`month` shows names)
#' @param y Column for the rows
#' @param value Column for the colour
#' @param annotate Write the value in each cell
#' @param cmap Diverging palette name from [ggplot2::scale_fill_distiller()]
#' @param title Plot title
#' @return ggplot object
#' @export
#' @examplesIf requireNamespace("ggplot2", quietly = TRUE)
#' plot_heatmap(cor(mtcars[, 1:4]), annotate = TRUE)
plot_heatmap <- function(data, x = NULL, y = NULL, value = NULL, annotate = FALSE,
                         cmap = "RdYlBu", title = NULL) {
  need_ggplot2()
  if (is.null(value)) {
    m <- as.matrix(data)
    data <- data.frame(
      .y = rep(rownames(m), times = ncol(m)),
      .x = rep(colnames(m), each = nrow(m)), .value = as.vector(m)
    )
    data$.x <- factor(data$.x, levels = colnames(m))
    data$.y <- factor(data$.y, levels = rev(rownames(m)))
    x <- ".x"
    y <- ".y"
    value <- ".value"
    legend <- NULL
  } else {
    data[[y]] <- factor(data[[y]], levels = rev(unique(data[[y]])))
    if (x == "month") data[[x]] <- factor(month.abb[data[[x]]], levels = month.abb)
    legend <- value
  }
  p <- ggplot2::ggplot(data, ggplot2::aes(x = .data[[x]], y = .data[[y]], fill = .data[[value]])) +
    ggplot2::geom_tile() +
    ggplot2::scale_fill_distiller(palette = cmap, name = legend) +
    ggplot2::labs(title = title, x = NULL, y = NULL) +
    theme_varunayan() +
    ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 45, hjust = 1))
  if (annotate) p <- p + ggplot2::geom_text(ggplot2::aes(label = sprintf("%.2f", .data[[value]])), size = 2.5)
  p
}
