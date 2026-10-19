# Make inst/extdata/climate_of_india.rds (needs CDS); run from the repo root.
devtools::load_all("R")

states_url <- "https://geo.bharatviz.org/geojsons/admin/India-geodata-lgd-states.geojson"

era5_t2m <- era5ify_geojson(
  request_id = "india_t2m_yearly",
  variables = "2m_temperature",
  start_date = "1941-01-01",
  end_date = "2024-12-31",
  json_file = states_url,
  frequency = "yearly",
  level = "union"
)
t2m_yearly <- spatial_mean(era5_t2m, "value", by = "year")
names(t2m_yearly)[names(t2m_yearly) == "value"] <- "t2m"

era5_tp <- era5ify_bbox(
  request_id = "tp_india_2000_2024",
  variables = "total_precipitation",
  start_date = "2000-01-01",
  end_date = "2024-12-31",
  north = 37.1, south = 6.3, east = 97.4, west = 68.1,
  frequency = "monthly",
  resolution = 0.25
)
peak <- peak_month(era5_tp, "value")

saveRDS(list(t2m_yearly = t2m_yearly, peak = peak),
  "R/inst/extdata/climate_of_india.rds",
  compress = "xz"
)
