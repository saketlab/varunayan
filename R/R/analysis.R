#' Analysis helpers used by the vignettes
#'
#' Each function takes a long data frame (one row per grid point and time
#' step, as returned by `era5ify_*()`, `imd_*()`, `hadex3_*()` and
#' `cru_ts_*()`) and returns a small data frame. The Python package has the
#' same functions with the same arguments. The file
#' `parity/cases.json` holds the test cases for both.
#'
#' @name analysis
#' @noRd
NULL

.INDIA_BOUNDARY_URLS <- c(
  state = "https://geo.bharatviz.org/geojsons/admin/India-geodata-lgd-states.geojson",
  district = "https://geo.bharatviz.org/geojsons/admin/India-geodata-lgd-districts.geojson"
)

# Group means etc. with data.table, sorted by the group columns.
group_apply <- function(data, by, cols, fun) {
  dt <- data.table::as.data.table(data)
  if (length(by) == 0) {
    out <- dt[, lapply(.SD, fun), .SDcols = cols]
  } else {
    out <- dt[, lapply(.SD, fun), by = by, .SDcols = cols]
    data.table::setorderv(out, by)
  }
  as.data.frame(out)
}

mean_na <- function(x) mean(x, na.rm = TRUE)

#' Load India state or district boundaries
#'
#' Downloads the India LGD boundaries from geo.bharatviz.org once and keeps
#' them in the package cache.
#'
#' @param level `"state"` or `"district"`
#' @return sf object (CRS 4326) with `state_name` (and `district_name` for
#'   districts)
#' @export
#' @examples
#' \donttest{
#' states <- load_india_boundaries("state")
#' }
load_india_boundaries <- function(level = c("state", "district")) {
  level <- match.arg(level)
  path <- file.path(get_cache_dir(), sprintf("india_lgd_%ss.geojson", level))
  if (!file.exists(path)) {
    message("Downloading India ", level, " boundaries")
    utils::download.file(.INDIA_BOUNDARY_URLS[[level]], path, mode = "wb", quiet = TRUE)
  }
  sf::st_transform(sf::st_read(path, quiet = TRUE), 4326)
}

#' Spatial mean over grid points
#'
#' @param data Long data frame with a latitude column and the `by` columns
#' @param value Name of the column to average
#' @param by Group columns, for example `c("year", "month")` or `"year"`
#' @param weight `"coslat"` weights each point by cos(latitude), so that
#'   points near the poles count less. `NULL` gives a plain mean.
#' @param lat_col Name of the latitude column
#' @return Data frame with the `by` columns and `value`. A `date` column is
#'   added when `by` holds `year` and `month`.
#' @export
#' @examples
#' grid <- expand.grid(latitude = c(10, 20), longitude = 70, year = 2000, month = 1:2)
#' grid$t2m <- c(20, 30, 21, 31)
#' spatial_mean(grid, "t2m")
spatial_mean <- function(data, value, by = c("year", "month"), weight = "coslat",
                         lat_col = "latitude") {
  by <- unlist(by)
  df <- data[!is.na(data[[value]]), , drop = FALSE]
  if (is.null(weight)) {
    w <- rep(1, nrow(df))
  } else if (identical(weight, "coslat")) {
    w <- cos(df[[lat_col]] * pi / 180)
  } else {
    stop("weight must be 'coslat' or NULL")
  }
  tmp <- data.frame(wv = df[[value]] * w, w = w)
  tmp[by] <- df[by]
  out <- group_apply(tmp, by, c("wv", "w"), sum)
  out[[value]] <- out$wv / out$w
  out <- out[c(by, value)]
  if (all(c("year", "month") %in% by)) {
    out$date <- as.Date(sprintf("%04d-%02d-01", as.integer(out$year), as.integer(out$month)))
  }
  out
}

#' Agreement statistics between two columns
#'
#' Rows where `x` or `y` is missing are removed first.
#'
#' @param data Data frame with the two columns, for example after a merge
#' @param x First column (for example the reference dataset)
#' @param y Second column
#' @param by Optional group columns, for example `"state_name"`
#' @return Data frame with the `by` columns, `n`, `r` (Pearson), `bias`
#'   (mean of y - x) and `rmse`
#' @export
#' @examples
#' df <- data.frame(imd = c(1, 2, 3, 4), era5 = c(1.1, 2.3, 2.9, 4.2))
#' compare(df, "imd", "era5")
compare <- function(data, x, y, by = NULL) {
  by <- unlist(by)
  df <- data[!is.na(data[[x]]) & !is.na(data[[y]]), , drop = FALSE]
  stats_one <- function(xv, yv) {
    d <- yv - xv
    r <- if (length(xv) > 1) suppressWarnings(stats::cor(xv, yv)) else NA_real_
    list(n = length(xv), r = r, bias = mean(d), rmse = sqrt(mean(d^2)))
  }
  # .SD avoids a clash when a column is named "x" or "y".
  dt <- data.table::as.data.table(df)
  if (length(by) == 0) {
    out <- dt[, stats_one(.SD[[1]], .SD[[2]]), .SDcols = c(x, y)]
  } else {
    out <- dt[, stats_one(.SD[[1]], .SD[[2]]), by = by, .SDcols = c(x, y)]
    data.table::setorderv(out, by)
  }
  out <- as.data.frame(out)
  out$n <- as.integer(out$n)
  out
}

#' Cross-correlation of two series
#'
#' This is [stats::ccf()] as a data frame. `r` at lag `k` estimates
#' cor(x\[t + k\], y\[t\]). A peak at a negative lag means that `x` changes
#' before `y`.
#'
#' @param x First series
#' @param y Second series, same length as `x`
#' @param max_lag Largest lag to return, in steps
#' @return Data frame with `lag` (-max_lag to max_lag) and `r`
#' @export
#' @examples
#' rain <- sin(1:48 / 2)
#' searches <- c(rain[-1], 0)
#' cross_correlation(searches, rain, max_lag = 3)
cross_correlation <- function(x, y, max_lag = 12) {
  if (length(x) != length(y)) stop("x and y must have the same length")
  cc <- stats::ccf(as.numeric(x), as.numeric(y), lag.max = max_lag, plot = FALSE)
  data.frame(lag = as.integer(cc$lag), r = as.numeric(cc$acf))
}

#' Departure from the mean over a baseline period
#'
#' @param data Data frame with `value` (and `year_col` if a baseline is set)
#' @param value Name of the column to use
#' @param baseline Optional `c(first_year, last_year)`. The default uses all rows.
#' @param year_col Name of the year column for the baseline
#' @return Numeric vector of anomalies, one for each row of `data`
#' @export
#' @examples
#' df <- data.frame(year = 2001:2005, t2m = c(25, 26, 25.5, 27, 26.5))
#' anomaly(df, "t2m")
anomaly <- function(data, value, baseline = NULL, year_col = "year") {
  ref <- data[[value]]
  if (!is.null(baseline)) {
    yr <- data[[year_col]]
    ref <- ref[yr >= baseline[[1]] & yr <= baseline[[2]]]
  }
  data[[value]] - mean(ref, na.rm = TRUE)
}

#' Mean for each calendar month
#'
#' @param data Data frame with a `month` column (1-12)
#' @param value Name of the column to average
#' @param by Optional group columns, for example `"country"`
#' @return Data frame with the `by` columns, `month` and `value`
#' @export
#' @examples
#' df <- data.frame(month = rep(1:12, 2), t2m = c(1:12, 3:14))
#' seasonal_cycle(df, "t2m")
seasonal_cycle <- function(data, value, by = NULL) {
  group_apply(data, c(unlist(by), "month"), value, mean_na)
}

#' Month of the largest long-term mean
#'
#' @param data Data frame with `month` and the `by` columns
#' @param value Name of the column to use, for example monthly precipitation
#' @param by Group columns. The default is each grid point.
#' @return Data frame with the `by` columns, `peak_month` (1-12),
#'   `peak_value` and `annual_total` (sum of the 12 monthly means). When two
#'   months have the same mean, the first month is the peak.
#' @export
#' @examples
#' df <- data.frame(latitude = 10, longitude = 70, month = 1:12, tp = c(1:6, 12:7))
#' peak_month(df, "tp")
peak_month <- function(data, value, by = c("latitude", "longitude")) {
  by <- unlist(by)
  clim <- data.table::as.data.table(seasonal_cycle(data, value, by = by))
  out <- clim[, list(
    peak_month = .SD[[1]][which.max(.SD[[2]])],
    peak_value = max(.SD[[2]]),
    annual_total = sum(.SD[[2]])
  ), by = by, .SDcols = c("month", value)]
  data.table::setorderv(out, by)
  out <- as.data.frame(out)
  out$peak_month <- as.integer(out$peak_month)
  out
}

#' Seasonal total or mean, averaged over years
#'
#' For each group and year, the function takes the sum or mean of the
#' selected months. Then it calculates the mean over the years.
#'
#' @param data Data frame with `year`, `month` (or `date`) and the `by` columns
#' @param value Name of the column to use
#' @param months Months of the season, for example `6:8`
#' @param how `"sum"` (seasonal total) or `"mean"`
#' @param by Group columns. The default is each grid point.
#' @return Data frame with the `by` columns and `value`
#' @export
#' @examples
#' df <- expand.grid(latitude = 10, longitude = 70, year = 2001:2002, month = 1:12)
#' df$tp <- seq_len(nrow(df))
#' seasonal_stat(df, "tp", months = 6:8)
seasonal_stat <- function(data, value, months, how = c("sum", "mean"),
                          by = c("latitude", "longitude")) {
  how <- match.arg(how)
  by <- unlist(by)
  if (!all(c("year", "month") %in% names(data))) {
    dates <- as.Date(data$date)
    data$year <- as.integer(format(dates, "%Y"))
    data$month <- as.integer(format(dates, "%m"))
  }
  df <- data[data$month %in% unlist(months), , drop = FALSE]
  fun <- if (how == "sum") function(x) sum(x, na.rm = TRUE) else mean_na
  per_year <- group_apply(df, c(by, "year"), value, fun)
  group_apply(per_year, by, value, mean_na)
}

#' Average onto a coarser regular grid
#'
#' Each point goes into the cell of size `resolution` that contains it. The
#' result has the cell centres, so a 0.5 degree grid has centres at x.25 and
#' x.75, the same as CRU TS.
#'
#' @param data Data frame with latitude and longitude columns
#' @param value Name of the column to average
#' @param resolution Target cell size in degrees
#' @param by Optional extra group columns, for example `"year"`
#' @param lat_col Name of the latitude column
#' @param lon_col Name of the longitude column
#' @return Data frame with `lat_col`, `lon_col`, the `by` columns and `value`
#' @export
#' @examples
#' df <- expand.grid(latitude = seq(10, 10.75, 0.25), longitude = seq(70, 70.75, 0.25))
#' df$t2m <- seq_len(nrow(df))
#' regrid(df, "t2m", resolution = 0.5)
regrid <- function(data, value, resolution, by = NULL,
                   lat_col = "latitude", lon_col = "longitude") {
  # The small offset keeps 0.3 / 0.1 = 2.9999... in cell 3.
  centre <- function(v) round(floor(v / resolution + 1e-9) * resolution + resolution / 2, 6)
  data[[lat_col]] <- centre(data[[lat_col]])
  data[[lon_col]] <- centre(data[[lon_col]])
  group_apply(data, c(lat_col, lon_col, unlist(by)), value, mean_na)
}
