devtools::load_all("R")

cities <- list(Mumbai = c(19.1375, 72.9151), Bengaluru = c(12.9214, 77.5025))
hourly <- do.call(rbind, lapply(names(cities), function(city) {
  d <- era5ify_point(
    request_id = paste0("diurnal_", tolower(city), "_2023"),
    variables = c("2m_temperature", "2m_dewpoint_temperature", "total_precipitation"),
    start_date = "2023-01-01",
    end_date = "2023-12-31",
    lat = cities[[city]][1], lon = cities[[city]][2],
    frequency = "hourly"
  )
  wide <- stats::reshape(
    as.data.frame(d[, c("datetime", "variable", "value")]),
    idvar = "datetime", timevar = "variable", direction = "wide"
  )
  names(wide) <- sub("^value\\.", "", names(wide))
  data.frame(
    city = city,
    time = wide$datetime,
    temp_c = wide$t2m,
    precip_mm = wide$tp,
    rh = relative_humidity_from_dewpoint(wide$t2m, wide$d2m)
  )
}))

saveRDS(hourly, "R/inst/extdata/diurnal_cycle.rds", compress = "xz")

# 2015-2024, reduced to days so the file stays small
daily <- do.call(rbind, lapply(names(cities), function(city) {
  d <- era5ify_point(
    request_id = paste0("radial_", tolower(city), "_2015_2024"),
    variables = c("2m_temperature", "total_precipitation"),
    start_date = "2015-01-01",
    end_date = "2024-12-31",
    lat = cities[[city]][1], lon = cities[[city]][2],
    frequency = "hourly"
  )
  d <- as.data.frame(d[, c("datetime", "variable", "value")])
  d$date <- as.Date(lubridate::with_tz(d$datetime, "Asia/Kolkata"))
  fn <- function(v) if (v == "tp") sum else mean
  out <- lapply(c("t2m", "tp"), function(v) {
    x <- d[d$variable == v, ]
    stats::aggregate(value ~ date, x, fn(v))
  })
  data.frame(
    city = city, date = out[[1]]$date, temp_c = out[[1]]$value,
    precip_mm = out[[2]]$value[match(out[[1]]$date, out[[2]]$date)]
  )
}))

saveRDS(daily, "R/inst/extdata/radial_years.rds", compress = "xz")
