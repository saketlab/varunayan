# Make inst/extdata/public_interest.rds (needs CDS); run from the repo root.
devtools::load_all("R")

# The article requests 2004-2024. The 2000-2024 request is the same as in
# climate-of-india, so it comes from the cache. Keep the years from 2004.
india <- era5ify_geojson(
  request_id = "tp_india_2000_2024",
  variables = "total_precipitation",
  start_date = "2000-01-01",
  end_date = "2024-12-31",
  json_file = "https://geo.bharatviz.org/geojsons/admin/India-geodata-lgd-states.geojson",
  frequency = "monthly",
  resolution = 0.25
)
india <- india[india$year >= 2004, ]
rain <- spatial_mean(india, "value", by = c("year", "month"))
names(rain)[names(rain) == "value"] <- "rainfall_mm"
jja <- seasonal_stat(india, "value", months = 6:8, how = "sum")

california <- era5ify_geojson(
  request_id = "t2m_california_2004_2024",
  variables = "2m_temperature",
  start_date = "2004-01-01",
  end_date = "2024-12-31",
  json_file = "https://gist.githubusercontent.com/JaggeryArray/50ad17645a290ee4445e1113609de5e4/raw/91e97ec6ae6654093490df87a9802e359bf303b1/california.geojson",
  frequency = "monthly",
  resolution = 0.25
)
temp <- spatial_mean(california, "value", by = c("year", "month"))
names(temp)[names(temp) == "value"] <- "t2m_c"

saveRDS(list(rain = rain, jja = jja, temp = temp),
  "R/inst/extdata/public_interest.rds",
  compress = "xz"
)
