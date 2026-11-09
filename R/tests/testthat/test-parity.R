# Run parity/cases.json; python/tests/test_parity.py runs the same cases.

cases_file <- testthat::test_path("..", "..", "..", "parity", "cases.json")
skip_if_not(file.exists(cases_file), "shared parity cases not found")
cases <- jsonlite::fromJSON(cases_file, simplifyVector = TRUE, simplifyDataFrame = FALSE)

na_from_null <- function(v) {
  if (is.list(v)) v <- vapply(v, function(e) if (is.null(e)) NA_real_ else as.numeric(e), numeric(1))
  if (is.logical(v)) v <- as.numeric(v)
  v
}

run_case <- function(case) {
  # era5_grid_output() is internal; every other function is exported.
  fn <- get(case$`function`, envir = asNamespace("varunayan"))
  args <- case$args
  # An empty JSON array means "no group columns".
  args <- lapply(args, function(a) if (is.list(a) && length(a) == 0) character(0) else a)
  if (!is.null(case$data)) {
    data <- as.data.frame(lapply(case$data, na_from_null), stringsAsFactors = FALSE)
    do.call(fn, c(list(data), args))
  } else {
    do.call(fn, args)
  }
}

for (case in cases) {
  test_that(paste("parity:", case$name), {
    got <- run_case(case)
    exp <- case$expected
    if (is.list(exp)) {
      expect_identical(names(got), names(exp))
      for (col in names(exp)) {
        if (col == "date") {
          expect_identical(format(got[[col]], "%Y-%m-%d"), unlist(exp[[col]]))
        } else if (col == "datetime") {
          expect_identical(format(got[[col]], "%Y-%m-%d %H:%M:%S", tz = "UTC"), unlist(exp[[col]]))
        } else if (is.character(exp[[col]])) {
          expect_identical(as.character(got[[col]]), exp[[col]])
        } else {
          expect_equal(as.numeric(got[[col]]), na_from_null(exp[[col]]),
            tolerance = case$tol, ignore_attr = TRUE, info = col
          )
        }
      }
    } else if (is.character(exp)) {
      expect_identical(as.character(got), exp)
    } else {
      expect_equal(as.numeric(got), na_from_null(exp), tolerance = case$tol)
    }
  })
}

test_that("parity cases cover every analysis function", {
  covered <- sort(unique(vapply(cases, function(c) c$`function`, character(1))))
  expect_identical(covered, sort(c(
    "spatial_mean", "compare", "cross_correlation", "anomaly", "seasonal_cycle",
    "peak_month", "seasonal_stat", "regrid", "dewpoint_from_relative_humidity",
    "era5_grid_output", "relative_humidity_from_dewpoint", "vapor_pressure_from_dewpoint",
    "wet_bulb_temperature", "wet_bulb_from_dewpoint", "heat_index", "heat_index_from_dewpoint",
    "humidex", "wbgt_simple", "wbgt_shade", "heat_index_risk_category", "wbgt_risk_category",
    "utci_category", "utci", "mean_radiant_temperature", "calc_heat_indices", "utci_sparse"
  )))
})

plot_cases <- jsonlite::fromJSON(sub("cases.json$", "plot_cases.json", cases_file),
  simplifyVector = TRUE, simplifyDataFrame = FALSE
)

for (case in plot_cases) {
  test_that(paste("parity plot:", case$name), {
    skip_if_not_installed("ggplot2")
    data <- as.data.frame(case$data, stringsAsFactors = FALSE)
    p <- do.call(getExportedValue("varunayan", case$`function`), c(list(data), case$args))
    expect_s3_class(p, "ggplot")
    built <- ggplot2::ggplot_build(p)
    expect_identical(length(unique(built$layout$layout$PANEL)), as.integer(case$expected$n_panels))
    labs <- ggplot2::get_labs(p)
    expect_identical(labs$title, case$expected$title)
    if (!is.null(case$expected$ylabel)) {
      ylab <- built$layout$panel_scales_y[[1]]$name
      if (is.null(ylab) || inherits(ylab, "waiver")) ylab <- labs$y
      expect_identical(ylab, case$expected$ylabel)
    }
  })
}

live_cases <- jsonlite::fromJSON(
  testthat::test_path("..", "..", "..", "parity", "live_cases.json"),
  simplifyVector = FALSE
)

expect_close <- function(got, expected, label) {
  expect_equal(as.numeric(got), na_from_null(expected), tolerance = 1e-9, ignore_attr = TRUE, info = label)
}

test_that("parity: METAR file", {
  case <- live_cases$metar_file
  out <- .parse_metar(case$text, unlist(case$prefixes))
  expect_identical(out$station_id, unlist(case$expected$station_id))
  expect_identical(format(out$observed_at, "%Y-%m-%d %H:%M:%S", tz = "UTC"), unlist(case$expected$observed_at))
  for (column in setdiff(names(case$expected), c("station_id", "observed_at"))) {
    expect_close(out[[column]], case$expected[[column]], column)
  }
})

test_that("parity: Open-Meteo block", {
  for (case in live_cases[c("open_meteo", "open_meteo_current")]) {
    out <- .parse_open_meteo(case$block, 19, 72)
    for (column in names(case$expected)) {
      expect_close(out[[column]], case$expected[[column]], column)
    }
  }
})

test_that("parity: METAR rain", {
  for (case in live_cases$metar_rain) {
    expect_identical(.metar_reports_rain(case$raw), case$rain, info = case$raw)
  }
})

test_that("parity: nearest airport", {
  case <- live_cases$nearest_airport
  now <- as.numeric(Sys.time())
  reports <- lapply(case$reports, function(r) {
    r$obsTime <- now - r$age_minutes * 60
    r$age_minutes <- NULL
    r
  })
  local_mocked_bindings(.live_get_json = function(url, query = list()) reports)
  got <- .live_metar(case$place)
  expected <- case$expected
  expect_identical(got$site, expected$site)
  for (field in c("distance_km", "temperature", "humidity", "wind_speed")) {
    expect_close(got[[field]], list(expected[[field]]), field)
  }
  expect_true(is.na(got$wind_direction))
  expect_identical(got$rain_reported, expected$rain_reported)
})

live_here <- list(latitude = 19, longitude = 72, label = "Here")

test_that("parity: OpenWeatherMap rain", {
  withr::local_envvar(OPENWEATHERMAP_API_KEY = "k")
  for (case in live_cases$openweathermap_rain) {
    local_mocked_bindings(.live_get_json = function(url, query = list()) case$payload)
    got <- .live_openweathermap(live_here)
    expect_close(got$rainfall, list(case$expected), "rainfall")
  }
})

test_that("parity: Weather Union rain", {
  withr::local_envvar(WEATHERUNION_API_KEY = "k")
  for (case in live_cases$weatherunion_rain) {
    local_mocked_bindings(
      weatherunion_stations = function(...) {
        data.frame(station_id = "S1", city = "C", name = "N", latitude = 19, longitude = 72)
      },
      weatherunion_weather = function(...) {
        data.frame(
          temperature = 30, humidity = 50, wind_speed = 1, wind_direction = 10,
          rain_intensity = .live_num(case$rain_intensity)
        )
      }
    )
    got <- .live_weatherunion(live_here)
    expect_close(got$rainfall, list(case$expected), "rainfall")
  }
})

test_that("parity: current weather columns", {
  case <- live_cases$current_weather
  local_mocked_bindings(open_meteo_weather = function(...) {
    do.call(data.frame, c(list(datetime = as.POSIXct("2026-11-09 09:15", tz = "UTC")), case$row))
  })
  out <- get_current_weather(latitude = 19, longitude = 72, source = "open-meteo")
  expect_identical(names(out), unlist(case$columns))
  expect_close(out$rainfall, list(case$row$rainfall), "rainfall")
})

test_that("parity: place names", {
  case <- live_cases$place_names
  expect_identical(.choose_place(case$results, case$query)$name, case$expected)
})

test_that("parity: live limits", {
  for (name in names(live_cases$limits)) {
    expect_equal(.live_limits[[name]], live_cases$limits[[name]], info = name)
  }
})

test_that("parity: METAR search box", {
  for (case in live_cases$metar_bbox) {
    expect_identical(.metar_bbox(list(latitude = case$latitude, longitude = case$longitude)), case$expected)
  }
})
