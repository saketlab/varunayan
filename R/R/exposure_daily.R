# Day-level heat exposure flags

.doy365 <- function(date) {
  d <- data.table::yday(date)
  d - (is_leap_year(data.table::year(date)) & d > 59L)
}

.in_baseline <- function(date, baseline) {
  yr <- data.table::year(date)
  yr >= baseline[1] & yr <= baseline[2]
}

.check_baseline <- function(date, baseline) {
  if (length(baseline) != 2L || baseline[1] > baseline[2]) {
    stop("baseline must be c(first_year, last_year)")
  }
  if (!any(.in_baseline(date, baseline))) {
    stop(sprintf("data contain no days in the baseline period %d-%d", baseline[1], baseline[2]))
  }
}

# baseline statistic per calendar day, pooled over +/- window days
.calendar_stat <- function(x, date, baseline, fun, window = 2L) {
  keep <- .in_baseline(date, baseline) & !is.na(x)
  offs <- seq.int(-window, window)
  target <- (rep(.doy365(date[keep]), each = length(offs)) - 1L + offs) %% 365L + 1L
  groups <- split(rep(x[keep], each = length(offs)), factor(target, levels = 1:365))
  thr <- vapply(groups, function(z) if (length(z)) fun(z) else NA_real_, numeric(1))
  thr[.doy365(date)]
}

.calendar_pct <- function(x, date, baseline, p, window = 2L) {
  .calendar_stat(x, date, baseline, function(z) stats::quantile(z, p, type = 8, names = FALSE), window)
}

# Runs of TRUE on consecutive dates lasting at least min_length days.
.spells <- function(flag, date, min_length) {
  flag[is.na(flag)] <- FALSE
  gap <- cumsum(c(TRUE, diff(as.integer(date)) != 1L))
  id <- data.table::rleid(flag, gap)
  len <- tabulate(id)[id]
  in_spell <- flag & len >= min_length
  start <- in_spell & !duplicated(id)
  list(in_spell = in_spell, start = start, length = ifelse(start, len, 0L))
}

.spell_frame <- function(date, flag, severe, min_length) {
  s <- .spells(flag, date, min_length)
  data.frame(
    date = date, day = s$in_spell, severe = s$in_spell & severe %in% TRUE,
    spell_start = s$start, spell_length = s$length
  )
}

.check_series <- function(date, ...) {
  date <- as.Date(date)
  if (anyNA(date)) stop("date contains NA")
  if (is.unsorted(date, strictly = TRUE)) stop("date must be strictly increasing (one location per call)")
  lens <- lengths(list(...))
  if (any(lens != length(date))) stop("all inputs must have the same length as date")
  date
}

#' Excess Heat Factor
#'
#' Excess Heat Factor (EHF) of Nairn & Fawcett (2015). Daily mean temperature
#' (DMT) pairs each day's maximum with the following night's minimum,
#' `T_i = (tmax_i + tmin_(i+1)) / 2`. For the three-day period starting on day
#' `i`, `EHI_sig = mean(T_i, T_i+1, T_i+2) - T95` and `EHI_accl = mean(T_i,
#' T_i+1, T_i+2) - mean(T_i-1, ..., T_i-30)`, with `T95` the 95th percentile of
#' DMT over the baseline years; `EHF = EHI_sig * max(1, EHI_accl)`. Positive EHF
#' marks heatwave conditions; `EHF85`, the 85th percentile of positive baseline
#' EHF values, is the severe threshold and `3 * EHF85` the extreme threshold.
#'
#' @param date Dates of a strictly increasing daily series for one location.
#'   Missing days leave the windows that span them `NA`.
#' @param tmax,tmin Daily maximum and minimum temperature (degrees Celsius).
#' @param baseline Climatology years, `c(first, last)`.
#' @return A data.frame with `date`, `dmt`, `ehi_sig`, `ehi_accl` and `ehf`
#'   (degrees Celsius squared), indexed by the first day of each three-day
#'   period, with attributes `t95` and `ehf85`. `NA` where the windows are
#'   incomplete.
#' @references Nairn, J.R. & Fawcett, R.J.B. (2015). The Excess Heat Factor: A
#'   Metric for Heatwave Intensity and Its Use in Classifying Heatwave
#'   Severity. International Journal of Environmental Research and Public
#'   Health, 12(1), 227-253. \doi{10.3390/ijerph120100227}
#' @export
#' @examples
#' d <- seq(as.Date("2001-01-01"), as.Date("2003-12-31"), by = "day")
#' doy <- as.POSIXlt(d)$yday
#' tmax <- 33 + 8 * sin(2 * pi * (doy - 80) / 365)
#' tmax[d >= as.Date("2003-05-10") & d <= as.Date("2003-05-16")] <- 47
#' ehf <- excess_heat_factor(d, tmax, tmax - 12, baseline = c(2001, 2002))
#' subset(ehf, ehf > 0 & date > as.Date("2003-05-01") & date < as.Date("2003-05-31"))
excess_heat_factor <- function(date, tmax, tmin, baseline) {
  date <- .check_series(date, tmax, tmin)
  .check_baseline(date, baseline)
  full <- seq(date[1], date[length(date)], by = "day")
  at <- match(full, date)
  dmt <- (tmax[at] + data.table::shift(tmin[at], -1L)) / 2
  base <- .in_baseline(full, baseline)
  t95 <- stats::quantile(dmt[base], 0.95, type = 8, na.rm = TRUE, names = FALSE)
  t3 <- data.table::frollmean(dmt, 3L, align = "left", algo = "exact")
  t30 <- data.table::shift(data.table::frollmean(dmt, 30L, algo = "exact"))
  ehi_sig <- t3 - t95
  ehi_accl <- t3 - t30
  ehf <- ehi_sig * pmax(1, ehi_accl)
  pos <- ehf[base & ehf > 0 & !is.na(ehf)]
  keep <- !is.na(at)
  out <- data.frame(date = date, dmt = dmt[keep], ehi_sig = ehi_sig[keep], ehi_accl = ehi_accl[keep], ehf = ehf[keep])
  attr(out, "t95") <- t95
  attr(out, "ehf85") <- if (length(pos)) stats::quantile(pos, 0.85, type = 8, names = FALSE) else NA_real_
  out
}

# Days covered by any flagged three-day period, indexed by its first day.
.cover3 <- function(hit, date) {
  starts <- date[hit %in% TRUE]
  date %in% c(starts, starts + 1L, starts + 2L)
}

#' Heatwave days
#'
#' Flags the days of a daily maximum temperature series that fall in a
#' heatwave, under one of three definitions:
#' * `"imd"`: India Meteorological Department. A day qualifies when Tmax is at
#'   least 40 C (plains), 37 C (coastal) or 30 C (hilly) and departs at least
#'   4.5 C from the calendar-day normal, or when Tmax is at least 45 C. Severe:
#'   departure above 6.4 C with Tmax at least 40 C (plains, coastal) or 30 C
#'   (hilly), or Tmax of at least 47 C. A heatwave needs `min_duration` (2)
#'   consecutive qualifying days. IMD also requires 2 stations in a
#'   meteorological sub-division; each series here is judged on its own.
#' * `"percentile"`: Tmax above the calendar-day `percentile` of the baseline
#'   years (5-day window) for at least `min_duration` (3) days, as in Rohini et
#'   al. (2016) for India.
#' * `"ehf"`: days covered by a three-day period with positive
#'   [excess_heat_factor()]; severe when EHF reaches EHF85.
#'
#' The calendar-day normal is the baseline mean over a `2 * window + 1` day
#' window. Percentiles use [stats::quantile()] type 8 without the in-base
#' bootstrap of the ETCCDI indices.
#'
#' @param date Dates of a strictly increasing daily series for one location.
#' @param tmax Daily maximum temperature (degrees Celsius).
#' @param tmin Daily minimum temperature; required for `method = "ehf"`.
#' @param method `"imd"`, `"percentile"` or `"ehf"`.
#' @param baseline Climatology years, `c(first, last)`, contained in `date`.
#' @param terrain For `"imd"`: `"plains"`, `"coastal"` or `"hilly"`; see
#'   [imd_terrain()] to classify a location.
#' @param percentile Threshold quantile for `"percentile"`.
#' @param min_duration Minimum run of qualifying days; defaults to 2 for
#'   `"imd"` and 3 for `"percentile"` and `"ehf"`.
#' @param window Half-width in days of the calendar-day window.
#' @return A data.frame with `date`, `day` (in a heatwave), `severe`,
#'   `spell_start` and `spell_length` (on the first day of each heatwave).
#' @references India Meteorological Department. Heat wave and warm night
#'   definitions. \url{https://mausam.imd.gov.in/pdfs/heatcolduser/Definition.pdf}
#'
#'   Rohini, P., Rajeevan, M. & Srivastava, A.K. (2016). On the Variability and
#'   Increasing Trends of Heat Waves over India. Scientific Reports, 6, 26153.
#'   \doi{10.1038/srep26153}
#' @export
#' @examples
#' d <- seq(as.Date("2001-01-01"), as.Date("2003-12-31"), by = "day")
#' doy <- as.POSIXlt(d)$yday
#' tmax <- 33 + 8 * sin(2 * pi * (doy - 80) / 365)
#' tmax[d >= as.Date("2003-05-10") & d <= as.Date("2003-05-13")] <- 46
#' hw <- heatwave_days(d, tmax, baseline = c(2001, 2002))
#' subset(hw, day)
heatwave_days <- function(date, tmax, tmin = NULL, method = c("imd", "percentile", "ehf"),
                          baseline = c(1991, 2020), terrain = c("plains", "coastal", "hilly"),
                          percentile = 0.9, min_duration = NULL, window = 2L) {
  method <- match.arg(method)
  date <- .check_series(date, tmax)
  .check_baseline(date, baseline)
  if (is.null(min_duration)) min_duration <- if (method == "imd") 2L else 3L
  flags <- switch(method,
    imd = {
      terrain <- match.arg(terrain)
      tmax_floor <- c(plains = 40, coastal = 37, hilly = 30)[[terrain]]
      # the coastal clause defines a heatwave only; severe keeps the plains floor
      severe_floor <- if (terrain == "coastal") 40 else tmax_floor
      dep <- .imd_departure(tmax, date, baseline, window)
      list(
        tmax >= tmax_floor & dep$flag | tmax >= 45,
        tmax >= severe_floor & dep$severe | tmax >= 47
      )
    },
    percentile = list(tmax > .calendar_pct(tmax, date, baseline, percentile, window), FALSE),
    ehf = {
      if (is.null(tmin)) stop("method = \"ehf\" needs tmin")
      e <- excess_heat_factor(date, tmax, tmin, baseline)
      list(.cover3(e$ehf > 0, date), .cover3(e$ehf >= attr(e, "ehf85"), date))
    }
  )
  .spell_frame(date, flags[[1]], flags[[2]], min_duration)
}

# IMD departure from the calendar-day normal: at least 4.5 C, severe above 6.4 C.
.imd_departure <- function(x, date, baseline, window) {
  dep <- x - .calendar_stat(x, date, baseline, mean, window)
  list(flag = dep >= 4.5, severe = dep > 6.4)
}

#' Warm nights
#'
#' Flags warm nights in a daily minimum temperature series:
#' * `"imd"`: India Meteorological Department. Tmax of at least 40 C and Tmin
#'   departing at least 4.5 C from the calendar-day normal; very warm (flagged
#'   `severe`) above 6.4 C.
#' * `"percentile"`: Tmin above the calendar-day `percentile` of the baseline
#'   years (ETCCDI TN90p with the default 0.9).
#' * `"absolute"`: Tmin above `threshold` (ETCCDI tropical nights, TR, with the
#'   default 20 C).
#'
#' @inheritParams heatwave_days
#' @param tmin Daily minimum temperature (degrees Celsius).
#' @param tmax Daily maximum temperature; required for `method = "imd"`.
#' @param method `"imd"`, `"percentile"` or `"absolute"`.
#' @param threshold Tmin threshold for `"absolute"` (degrees Celsius).
#' @param min_duration Minimum run of warm nights counted as a spell.
#' @return A data.frame with `date`, `day` (a warm night within a spell),
#'   `severe`, `spell_start` and `spell_length`.
#' @references India Meteorological Department. Heat wave and warm night
#'   definitions. \url{https://mausam.imd.gov.in/pdfs/heatcolduser/Definition.pdf}
#'
#'   Zhang, X., Alexander, L., Hegerl, G.C., Jones, P., Klein Tank, A.,
#'   Peterson, T.C., Trewin, B. & Zwiers, F.W. (2011). Indices for monitoring
#'   changes in extremes based on daily temperature and precipitation data.
#'   WIREs Climate Change, 2(6), 851-870. \doi{10.1002/wcc.147}
#' @export
#' @examples
#' d <- seq(as.Date("2001-01-01"), as.Date("2001-12-31"), by = "day")
#' tmin <- 22 + 6 * sin(2 * pi * (as.POSIXlt(d)$yday - 80) / 365)
#' wn <- warm_nights(d, tmin, method = "absolute", threshold = 27)
#' sum(wn$day)
warm_nights <- function(date, tmin, tmax = NULL, method = c("imd", "percentile", "absolute"),
                        baseline = c(1991, 2020), percentile = 0.9, threshold = 20,
                        min_duration = 1L, window = 2L) {
  method <- match.arg(method)
  date <- .check_series(date, tmin)
  if (method != "absolute") .check_baseline(date, baseline)
  flags <- switch(method,
    absolute = list(tmin > threshold, FALSE),
    percentile = list(tmin > .calendar_pct(tmin, date, baseline, percentile, window), FALSE),
    imd = {
      if (is.null(tmax)) stop("method = \"imd\" needs tmax")
      dep <- .imd_departure(tmin, date, baseline, window)
      list(tmax >= 40 & dep$flag, tmax >= 40 & dep$severe)
    }
  )
  .spell_frame(date, flags[[1]], flags[[2]], min_duration)
}
