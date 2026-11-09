test_that("temperature_only drops rain gauges", {
  all_stations <- weatherunion_stations()
  aws <- weatherunion_stations(temperature_only = TRUE)
  expect_setequal(all_stations$device_type, c("aws", "rain_gauge"))
  expect_setequal(aws$device_type, "aws")
  expect_lt(nrow(aws), nrow(all_stations))
})

test_that("weatherunion_weather needs a key", {
  expect_error(weatherunion_weather("A", api_key = ""), "WEATHERUNION_API_KEY")
})
