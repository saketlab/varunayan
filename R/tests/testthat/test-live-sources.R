metar_text <- paste(
  "raw_text,station_id,observation_time,latitude,longitude,temp_c,dewpoint_c,wind_dir_degrees,wind_speed_kt",
  "VABB 1,VABB,2026-11-09T09:00:00Z,19.1,72.8,30,20,VRB,10",
  "KJFK 1,KJFK,2026-11-09T09:00:00Z,40.6,-73.8,10,5,100,5",
  sep = "\n"
)

test_that(".parse_metar keeps prefixes and converts units", {
  out <- .parse_metar(metar_text, "VA")
  expect_equal(out$station_id, "VABB")
  expect_equal(out$wind_speed, 5.14444, tolerance = 1e-6)
  expect_true(is.na(out$wind_direction))
  expect_true(out$humidity > 50 && out$humidity < 60)
  expect_equal(format(out$observed_at, "%H:%M", tz = "UTC"), "09:00")
})

test_that(".parse_metar rejects a file with no header", {
  expect_error(.parse_metar("nothing here"), "no header")
})

test_that(".parse_open_meteo keeps gaps as NA", {
  out <- .parse_open_meteo(
    list(time = list("2024-01-01T00:00", "2024-01-01T01:00"), temperature_2m = list(10, NULL)),
    19, 72
  )
  expect_equal(nrow(out), 2L)
  expect_equal(out$temperature, c(10, NA))
  expect_true(all(is.na(out$humidity)))
})

test_that("open_meteo_weather needs both dates or neither", {
  expect_error(open_meteo_weather(1, 2, start_date = "2024-01-01"), "both")
})
