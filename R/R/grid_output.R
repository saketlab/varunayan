#' Turn the downloaded ERA5 grid into the output of era5ify_*()
#'
#' Each grid cell is aggregated in time with the method of its variable (sum,
#' max, min or mean). The monthly-means product gives the mean daily value of
#' an accumulated variable (for example precipitation), so such values are
#' multiplied by the number of days in the month: monthly and yearly data are
#' totals. The Python function `processing.grid_output.to_long_grid()` does
#' the same, and `parity/cases.json` checks that the two agree.
#'
#' @param data Long data frame: datetime, latitude, longitude, optional
#'   pressure_level, variable, value
#' @param frequency "hourly", "daily", "weekly", "monthly" or "yearly"
#' @param convert_units Convert Kelvin to Celsius and metres to mm
#' @return Data frame: datetime, latitude, longitude, (pressure_level),
#'   variable, value, and year (monthly, yearly) and month (monthly)
#' @noRd
era5_grid_output <- function(data, frequency, convert_units = TRUE) {
  dt <- data.table::as.data.table(data)
  dt[, datetime := as.POSIXct(datetime, tz = "UTC")]
  keys <- intersect(c("latitude", "longitude", "pressure_level"), names(dt))

  if (frequency %in% c("monthly", "yearly")) {
    vars <- unique(dt$variable)
    sums <- dt$variable %in% vars[vapply(vars, is_sum_var, logical(1))]
    days <- lubridate::days_in_month(dt$datetime)
    dt[sums, value := value * days[sums]]
  }

  if (frequency != "hourly") {
    d <- as.Date(dt$datetime, tz = "UTC")
    start <- switch(frequency,
      daily = d,
      # Weeks start on Monday, as pandas "W-SUN" periods.
      weekly = d - (as.integer(format(d, "%u")) - 1L),
      monthly = as.Date(format(d, "%Y-%m-01")),
      yearly = as.Date(format(d, "%Y-01-01")),
      stop("Unknown frequency '", frequency, "'")
    )
    dt[, datetime := as.POSIXct(format(start), tz = "UTC")]
    methods <- vapply(unique(dt$variable), .aggregation_method, character(1))
    agg <- function(v, how) {
      if (all(is.na(v))) {
        return(NA_real_)
      }
      switch(how,
        sum = sum(v, na.rm = TRUE),
        max = max(v, na.rm = TRUE),
        min = min(v, na.rm = TRUE),
        mean(v, na.rm = TRUE)
      )
    }
    dt <- dt[, list(value = agg(value, methods[[.BY$variable]])),
      by = c("datetime", keys, "variable")
    ]
  }

  if (frequency %in% c("monthly", "yearly")) dt[, year := as.integer(format(datetime, "%Y"))]
  if (frequency == "monthly") dt[, month := as.integer(format(datetime, "%m"))]
  out <- as.data.frame(dt)
  if (convert_units) out <- convert_era5_units(out)

  front <- c("datetime", keys, "variable", "value")
  out <- out[c(front, setdiff(names(out), front))]
  out <- out[do.call(order, out[c("datetime", keys, "variable")]), , drop = FALSE]
  rownames(out) <- NULL
  out
}
