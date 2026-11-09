place <- list(latitude = 19.09, longitude = 72.87, label = "Mumbai")

test_that("auto says why each source was passed", {
  withr::local_envvar(WEATHERUNION_API_KEY = NA, OPENWEATHERMAP_API_KEY = NA)
  local_mocked_bindings(
    .live_get_json = function(url, query = list()) list(),
    open_meteo_weather = function(latitude, longitude, ...) {
      data.frame(
        datetime = as.POSIXct("2026-11-09 09:15", tz = "UTC"), latitude = latitude,
        longitude = longitude, temperature = 12.5, humidity = 60, wind_speed = 2,
        wind_direction = 80
      )
    }
  )
  out <- get_current_weather(latitude = 19.09, longitude = 72.87)
  expect_identical(out$source, "open-meteo")
  expect_identical(out$kind, "model")
  expect_true(is.na(out$heat_index))
  skipped <- attr(out, "skipped")
  expect_match(skipped$weatherunion, "is not set")
  expect_match(skipped$openweathermap, "is not set")
  expect_match(skipped$metar, "no recent airport")
})

test_that("weatherunion tries at most three stations", {
  withr::local_envvar(WEATHERUNION_API_KEY = "k")
  calls <- 0L
  local_mocked_bindings(weatherunion_weather = function(id, ...) {
    calls <<- calls + 1L
    data.frame(temperature = NA_real_, humidity = NA_real_, wind_speed = NA_real_, wind_direction = NA_real_)
  })
  expect_error(.live_weatherunion(place), "nearest stations is reporting", class = "live_source_unavailable")
  expect_identical(calls, 3L)
})

test_that("an explicit metar request finds a far airport but auto does not", {
  now <- Sys.time()
  local_mocked_bindings(
    .live_get_json = function(url, query = list()) {
      if (!is.null(query$ids)) list(list(name = paste(query$ids, "Arpt"))) else list()
    },
    metar_observations = function(...) {
      data.frame(
        station_id = c("NEAR", "STALE", "FAR"),
        observed_at = c(now, now - 172800, now),
        latitude = c(31.1, 31.1, 40), longitude = c(76, 77.2, 80),
        temperature = c(20, 5, 1), humidity = 50, wind_speed = 1, wind_direction = 10
      )
    }
  )
  shimla <- list(latitude = 31.1, longitude = 77.17, label = "Shimla")
  expect_error(.live_metar(shimla), "within 50 km", class = "live_source_unavailable")
  got <- .live_metar_nearest(shimla)
  expect_identical(got$site, "NEAR Arpt")
  expect_gt(got$distance_km, 100)
})

test_that("an HTTP error keeps only the status", {
  expect_error(
    .live_try(stop("Unauthorized (HTTP 401) at https://x/?appid=secret")),
    "^HTTP 401$",
    class = "live_source_unavailable"
  )
})

test_that("get_location parses an IP reply and rejects unknown sources", {
  local_mocked_bindings(.live_get_json = function(url, query = list()) {
    list(loc = "19.09,72.87", city = "Mumbai", country = "IN")
  })
  out <- get_location()
  expect_equal(out$latitude, 19.09)
  expect_match(out$label, "from IP")
  expect_error(get_current_weather(source = "nope"), "Unknown source")
})
