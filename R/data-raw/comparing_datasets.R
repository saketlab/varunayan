# Make inst/extdata/comparing_datasets.rds (needs CDS); run from the repo root.
devtools::load_all("R")

states_url <- "https://geo.bharatviz.org/geojsons/admin/India-geodata-lgd-states.geojson"
states <- load_india_boundaries("state")

# Monthly rainfall in each state, 2000-2024.
era5_rain <- era5ify_geojson(
  request_id = "era5_india_states_rain",
  variables = "total_precipitation",
  start_date = "2000-01-01",
  end_date = "2024-12-31",
  json_file = states_url,
  frequency = "monthly",
  resolution = 0.25,
  level = "feature"
)
imd_rain <- imd_rainfall_bbox(
  request_id = "imd_india_rain",
  start_year = 2000, end_year = 2024,
  north = 38.5, south = 6.5, east = 100, west = 66.5,
  frequency = "monthly"
)
imd_states <- aggregate_to_polygons(imd_rain, states, c(imd = "rainfall"),
  method = "point_in_polygon", polygon_id_cols = "state_name",
  by = "date", fill_empty = TRUE
)
era5_rain$date <- as.Date(era5_rain$datetime)
era5_rain$era5 <- era5_rain$value
rain <- merge(era5_rain[c("state_name", "date", "era5")], imd_states)

# Daily temperature extremes in Maharashtra, 2020.
# CDS refuses one request for the full year ("cost limits exceeded"), so
# request one month at a time.
month_starts <- seq(as.Date("2020-01-01"), as.Date("2020-12-01"), by = "month")
era5_temp <- do.call(rbind, lapply(month_starts, function(m) {
  era5ify_bbox(
    request_id = paste0("era5_maharashtra_tmax_tmin_", format(m, "%m")),
    variables = c(
      "maximum_2m_temperature_since_previous_post_processing",
      "minimum_2m_temperature_since_previous_post_processing"
    ),
    start_date = format(m), end_date = format(seq(m, by = "month", length.out = 2)[2] - 1),
    north = 21.75, south = 15, east = 80.75, west = 72,
    frequency = "hourly", resolution = 0.25
  )
}))
dt <- data.table::as.data.table(era5_temp)
dt[, date := as.Date(datetime)]
daily <- dt[, list(value = if (variable[1] == "mx2t") max(value) else min(value)),
  by = c("date", "latitude", "longitude", "variable")
]
rm(dt, era5_temp)
daily <- regrid(as.data.frame(daily), "value", 1, by = c("date", "variable"))
names(daily)[names(daily) == "value"] <- "era5"

imd_tmax <- imd_temperature_bbox("imd_mh_tmax", 2020, 2020,
  var_type = "tmax",
  north = 21.5, south = 15.5, east = 80.5, west = 72.5
)
imd_tmin <- imd_temperature_bbox("imd_mh_tmin", 2020, 2020,
  var_type = "tmin",
  north = 21.5, south = 15.5, east = 80.5, west = 72.5
)
keys <- c("date", "latitude", "longitude")
pair <- function(era5_var, imd) {
  out <- merge(daily[daily$variable == era5_var, c(keys, "era5")], imd, by = keys)
  names(out)[names(out) == "temperature"] <- "imd"
  out$era5 <- round(out$era5, 2)
  out$imd <- round(out$imd, 2)
  out[c(keys, "era5", "imd")]
}
tmax <- pair("mx2t", imd_tmax)
tmin <- pair("mn2t", imd_tmin)

# Monthly temperature over India, ERA5 and CRU TS, 2000-2018.
era5_t2m <- era5ify_bbox(
  request_id = "india_era5_t2m_monthly", variables = "2m_temperature",
  start_date = "2000-01-01", end_date = "2018-12-31",
  north = 37, south = 6, east = 98, west = 68, frequency = "monthly"
)
cru <- cru_ts_bbox(
  variable = "tmp", start_year = 2000, end_year = 2018,
  north = 37, south = 6, east = 98, west = 68
)
names(cru)[names(cru) == "value"] <- "cru"
cru_both <- merge(regrid(era5_t2m, "value", 0.5, by = c("year", "month")),
  cru[c("year", "month", "latitude", "longitude", "cru")],
  by = c("year", "month", "latitude", "longitude")
)
names(cru_both)[names(cru_both) == "value"] <- "era5"
cru_monthly <- merge(spatial_mean(cru_both, "era5"), spatial_mean(cru_both, "cru"))
cru_both$bias <- cru_both$era5 - cru_both$cru
cru_cells <- seasonal_stat(cru_both, "bias", months = 1:12, how = "mean")

saveRDS(
  list(rain = rain, tmax = tmax, tmin = tmin, cru_monthly = cru_monthly, cru_cells = cru_cells),
  "R/inst/extdata/comparing_datasets.rds",
  compress = "xz"
)
