#' Heat exposure indicators
#'
#' Summarizes daily temperature (and optionally humidity) into heat exposure
#' indicators per location and year or month, as used in heat-health
#' vulnerability indices: heatwave and warm-night frequency and duration,
#' diurnal temperature range, WBGT, heat index and wet-bulb temperature, plus
#' the ETCCDI indices TX90p, TN90p, WSDI and tropical nights.
#'
#' `data` needs columns `date`, `tmax` and `tmin` (degrees Celsius), one row
#' per day per location, covering the `baseline` years. With a `dewpoint`
#' column (degrees Celsius), afternoon humidity metrics are computed from
#' `tmax` and `dewpoint`: WBGT by [wbgt_simple()], heat index and wet-bulb
#' temperature. A `wbgt` column, such as daily maxima of [wbgt_liljegren()],
#' replaces the [wbgt_simple()] estimate.
#'
#' Spells are found on the full series, so a heatwave spanning two periods
#' counts as an event in the period where it starts and its days count where
#' they fall. `months` filters the summary.
#'
#' @param data A data.frame of daily values; see Details.
#' @param by Columns identifying a location, or `NULL` for a single series.
#' @param period Summarize by `"year"` or `"month"`.
#' @param months Months (1-12) to include, e.g. `3:6` for the Indian hot
#'   season; `NULL` for all.
#' @param baseline Climatology years, `c(first, last)`, for normals and
#'   percentiles.
#' @param heatwave_method Passed to [heatwave_days()] as `method`.
#' @param warm_night_method Passed to [warm_nights()] as `method`.
#' @param terrain Passed to [heatwave_days()] for the IMD definition.
#'   `"auto"` classifies each location with [imd_terrain()] from its
#'   `latitude` and `longitude` columns and adds a `terrain` column.
#' @param hill_elevation,cell_size Passed to [imd_terrain()] when
#'   `terrain = "auto"`.
#' @return A data.frame with one row per location and period and columns:
#'   \describe{
#'     \item{n_days}{days with data}
#'     \item{tmax_mean, tmin_mean}{mean daily maximum and minimum temperature}
#'     \item{dtr_mean}{mean diurnal temperature range (ETCCDI DTR)}
#'     \item{hot_days}{days with Tmax of at least 40 C}
#'     \item{tropical_nights}{nights with Tmin above 20 C (ETCCDI TR)}
#'     \item{tx90p, tn90p}{percent of days above the calendar-day 90th percentile of Tmax and Tmin}
#'     \item{wsdi}{days in runs of at least 6 days with Tmax above its 90th percentile (ETCCDI WSDI)}
#'     \item{heatwave_days, heatwave_events, heatwave_longest, severe_heatwave_days}{heatwave
#'       duration (total days), frequency (events starting in the period), longest event and
#'       severe days, from [heatwave_days()]}
#'     \item{warm_nights, warm_night_spells, warm_night_longest, very_warm_nights}{the same
#'       for [warm_nights()]}
#'   }
#'   With humidity: `wbgt_mean`, `wbgt_max`, `wbgt_days_high` (WBGT of at
#'   least 29.4 C, 85 F) and `wbgt_days_extreme` (at least 31.1 C, 88 F),
#'   `heat_index_max`, `heat_index_days_danger` (at least 39.4 C, 103 F),
#'   `wet_bulb_max` and `wet_bulb_days_31` (wet bulb of at least 31 C, near the
#'   30.55 C mean critical limit of Vecellio et al. 2022).
#' @references Vecellio, D.J., Wolf, S.T., Cottle, R.M. & Kenney, W.L. (2022).
#'   Evaluating the 35 C wet-bulb temperature adaptability threshold for young,
#'   healthy subjects (PSU HEAT Project). Journal of Applied Physiology, 132(2),
#'   340-345. \doi{10.1152/japplphysiol.00738.2021}
#' @seealso [imd_exposure_bbox()] to download IMD data and compute these in one
#'   call; [ndvi()] and [ndbi()] for the land-surface indicators.
#' @export
#' @examples
#' d <- seq(as.Date("2001-01-01"), as.Date("2004-12-31"), by = "day")
#' doy <- as.POSIXlt(d)$yday
#' tmax <- 33 + 8 * sin(2 * pi * (doy - 80) / 365)
#' tmax[d >= as.Date("2004-05-10") & d <= as.Date("2004-05-14")] <- 46.5
#' daily <- data.frame(date = d, tmax = tmax, tmin = tmax - 13, dewpoint = 18)
#' exposure_indicators(daily, by = NULL, baseline = c(2001, 2003), terrain = "plains")
#'
#' # Jaipur: terrain looked up from the coordinates
#' daily$latitude <- 26.9
#' daily$longitude <- 75.8
#' exposure_indicators(daily, baseline = c(2001, 2003))
exposure_indicators <- function(data, by = c("latitude", "longitude"),
                                period = c("year", "month"), months = NULL,
                                baseline = c(1991, 2020),
                                heatwave_method = c("imd", "percentile", "ehf"),
                                warm_night_method = c("imd", "percentile", "absolute"),
                                terrain = c("auto", "plains", "coastal", "hilly"),
                                hill_elevation = 1200, cell_size = NULL) {
  period <- match.arg(period)
  heatwave_method <- match.arg(heatwave_method)
  warm_night_method <- match.arg(warm_night_method)
  terrain <- match.arg(terrain)
  missing_cols <- setdiff(c("date", "tmax", "tmin", by), names(data))
  if (length(missing_cols)) stop("data is missing column(s): ", paste(missing_cols, collapse = ", "))

  dt <- data.table::as.data.table(data)
  dt[, date := as.Date(date)]
  auto <- terrain == "auto" && heatwave_method == "imd"
  if (auto) {
    if (!all(c("latitude", "longitude") %in% names(dt))) {
      stop("terrain = \"auto\" needs latitude and longitude columns; otherwise set terrain")
    }
    loc <- unique(dt[, c("latitude", "longitude")])
    loc[, terrain := imd_terrain(latitude, longitude, hill_elevation, cell_size)]
    off <- loc[is.na(terrain)]
    if (nrow(off)) {
      stop(
        "no IMD terrain for ", nrow(off), " location(s) outside the IMD land grid, e.g. ",
        off$latitude[1], ", ", off$longitude[1], "; set terrain"
      )
    }
    dt[loc, terrain := i.terrain, on = c("latitude", "longitude")]
    by <- c(by, "terrain")
  }
  daily <- dt[, .exposure_daily(.SD, baseline, heatwave_method, warm_night_method, if (auto) .BY$terrain else terrain),
    by = by
  ]
  daily[, `:=`(year = data.table::year(date), month = data.table::month(date))]
  if (!is.null(months)) daily <- daily[month %in% months]
  keys <- c(by, "year", if (period == "month") "month")
  out <- daily[, eval(.exposure_summary(names(daily))), by = keys]
  out[, `:=`(tx90p = 100 * tx90p, tn90p = 100 * tn90p)]
  for (v in intersect(c("wbgt_max", "heat_index_max", "wet_bulb_max"), names(out))) {
    data.table::set(out, which(is.infinite(out[[v]])), v, NA_real_)
  }
  data.table::setorderv(out, keys)
  as.data.frame(out)
}

.exposure_daily <- function(d, baseline, heatwave_method, warm_night_method, terrain) {
  d <- d[order(date)]
  if (anyDuplicated(d$date)) stop("duplicate dates within a location; check `by`")
  hw <- heatwave_days(d$date, d$tmax, d$tmin, heatwave_method, baseline, terrain)
  wn <- warm_nights(d$date, d$tmin, d$tmax, warm_night_method, baseline)
  tx90 <- d$tmax > .calendar_pct(d$tmax, d$date, baseline, 0.9)

  out <- data.table::data.table(
    date = d$date, tmax = d$tmax, tmin = d$tmin, dtr = d$tmax - d$tmin,
    has_data = !is.na(d$tmax) | !is.na(d$tmin), hot = d$tmax >= 40, trop = d$tmin > 20,
    tx90 = tx90, tn90 = d$tmin > .calendar_pct(d$tmin, d$date, baseline, 0.9),
    wsdi = .spells(tx90, d$date, 6L)$in_spell,
    hw_day = hw$day, hw_event = hw$spell_start, hw_len = hw$spell_length, hw_severe = hw$severe,
    wn_day = wn$day, wn_event = wn$spell_start, wn_len = wn$spell_length, wn_severe = wn$severe
  )
  has_dew <- "dewpoint" %in% names(d)
  wbgt <- if ("wbgt" %in% names(d)) d$wbgt else if (has_dew) wbgt_simple(d$tmax, d$dewpoint)
  if (!is.null(wbgt)) {
    out[, `:=`(wbgt = wbgt, wbgt_high = wbgt >= .WBGT_BREAKS[3], wbgt_extreme = wbgt >= .WBGT_BREAKS[4])]
  }
  if (has_dew) {
    rh <- relative_humidity_from_dewpoint(d$tmax, d$dewpoint)
    hi <- heat_index(d$tmax, rh)
    tw <- wet_bulb_temperature(d$tmax, rh)
    out[, `:=`(heat_index = hi, hi_danger = hi >= .HI_BREAKS[3], wet_bulb = tw, tw31 = tw >= 31)]
  }
  out
}

# plain reductions keep GForce; without it, all-NA max() is -Inf, reset by caller
.exposure_summary <- function(cols) {
  e <- alist(
    n_days = sum(has_data),
    tmax_mean = mean(tmax, na.rm = TRUE),
    tmin_mean = mean(tmin, na.rm = TRUE),
    dtr_mean = mean(dtr, na.rm = TRUE),
    hot_days = sum(hot, na.rm = TRUE),
    tropical_nights = sum(trop, na.rm = TRUE),
    tx90p = mean(tx90, na.rm = TRUE),
    tn90p = mean(tn90, na.rm = TRUE),
    wsdi = sum(wsdi),
    heatwave_days = sum(hw_day),
    heatwave_events = sum(hw_event),
    heatwave_longest = max(hw_len),
    severe_heatwave_days = sum(hw_severe),
    warm_nights = sum(wn_day),
    warm_night_spells = sum(wn_event),
    warm_night_longest = max(wn_len),
    very_warm_nights = sum(wn_severe)
  )
  if ("wbgt" %in% cols) {
    e <- c(e, alist(
      wbgt_mean = mean(wbgt, na.rm = TRUE),
      wbgt_max = max(wbgt, na.rm = TRUE),
      wbgt_days_high = sum(wbgt_high, na.rm = TRUE),
      wbgt_days_extreme = sum(wbgt_extreme, na.rm = TRUE)
    ))
  }
  if ("heat_index" %in% cols) {
    e <- c(e, alist(
      heat_index_max = max(heat_index, na.rm = TRUE),
      heat_index_days_danger = sum(hi_danger, na.rm = TRUE),
      wet_bulb_max = max(wet_bulb, na.rm = TRUE),
      wet_bulb_days_31 = sum(tw31, na.rm = TRUE)
    ))
  }
  as.call(c(quote(list), e))
}

#' IMD heat exposure indicators for a bounding box
#'
#' Downloads IMD gridded daily maximum and minimum temperature (1 degree) for
#' the requested years and the baseline, then computes
#' [exposure_indicators()] for each grid cell.
#'
#' @inheritParams imd_temperature_bbox
#' @inheritParams exposure_indicators
#' @param start_year,end_year Years to report (1951-2025).
#' @param ... Further arguments to [exposure_indicators()], such as `months`,
#'   `period`, `heatwave_method`, `terrain` or `hill_elevation`; terrain is
#'   classified per 1 degree cell.
#' @return The data.frame of [exposure_indicators()] for `start_year` to
#'   `end_year`, one row per grid cell (`latitude`, `longitude`) and period.
#' @export
#' @examplesIf interactive()
#' jaipur <- imd_exposure_bbox(2022, 2024,
#'   north = 28, south = 26,
#'   east = 77, west = 75, months = 3:6
#' )
imd_exposure_bbox <- function(start_year, end_year, north, south, east, west,
                              baseline = c(1991, 2020), ...,
                              output_dir = tempdir(), use_cache = TRUE) {
  yrs <- range(c(start_year, end_year, baseline))
  daily <- .imd_daily_tmax_tmin(yrs, north, south, east, west, output_dir, use_cache)
  out <- exposure_indicators(daily, baseline = baseline, cell_size = 1, ...)
  out[out$year >= start_year & out$year <= end_year, , drop = FALSE]
}

# daily IMD tmax and tmin for years yrs[1] to yrs[2], one row per cell and date
.imd_daily_tmax_tmin <- function(yrs, north, south, east, west, output_dir = tempdir(), use_cache = TRUE) {
  get <- function(var) {
    x <- data.table::as.data.table(imd_temperature_bbox(
      paste0("exposure_", var), yrs[1], yrs[2], north, south, east, west,
      var_type = var, frequency = "daily", output_dir = output_dir, use_cache = use_cache
    ))
    x[, date := as.Date(date)]
    data.table::setnames(x, "temperature", var)
  }
  merge(get("tmax"), get("tmin"), by = c("date", "latitude", "longitude"))
}
