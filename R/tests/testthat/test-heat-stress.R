# download wrappers are tested by mocking era5ify_bbox()/era5ify_geojson()

test_that("relative_humidity_from_dewpoint matches Magnus-Tetens and is bounded", {
  expect_equal(relative_humidity_from_dewpoint(25, 25), 100)
  # Dewpoint above air temperature is physically impossible; result is capped.
  expect_equal(relative_humidity_from_dewpoint(25, 30), 100)
  # T = 30, Td = 20 -> ~55%
  expect_equal(relative_humidity_from_dewpoint(30, 20), 55.08, tolerance = 1e-3)
  # T = 20, Td = 10 -> ~52.5%
  expect_equal(relative_humidity_from_dewpoint(20, 10), 52.5, tolerance = 1e-2)

  rh <- relative_humidity_from_dewpoint(rep(30, 5), c(0, 5, 10, 15, 20))
  expect_length(rh, 5)
  expect_true(all(diff(rh) > 0))
  expect_true(all(rh >= 0 & rh <= 100))
  expect_true(is.na(relative_humidity_from_dewpoint(NA_real_, 10)))
})

test_that("vapor_pressure_from_dewpoint gives standard saturation pressures", {
  expect_equal(vapor_pressure_from_dewpoint(0), 6.112)
  expect_equal(vapor_pressure_from_dewpoint(20), 23.37, tolerance = 1e-3)
  expect_equal(vapor_pressure_from_dewpoint(30), 42.47, tolerance = 2e-3)
  vp <- vapor_pressure_from_dewpoint(c(-10, 0, 10, 20, 30))
  expect_true(all(diff(vp) > 0))
})

test_that("wet_bulb_temperature reproduces Stull (2011) reference values", {
  # Stull (2011): T = 20 C, RH = 50 % -> Tw = 13.7 C
  expect_equal(wet_bulb_temperature(20, 50), 13.7, tolerance = 1e-2)
  expect_equal(wet_bulb_temperature(30, 60), 24.0, tolerance = 5e-3)

  # Wet bulb never exceeds dry bulb, and approaches it at saturation
  t <- c(10, 20, 30, 40)
  expect_true(all(wet_bulb_temperature(t, 50) < t))
  expect_equal(wet_bulb_temperature(25, 99), 25, tolerance = 0.02)

  # Monotone in both T and RH
  expect_true(all(diff(wet_bulb_temperature(30, c(10, 30, 50, 70, 90))) > 0))
  expect_true(all(diff(wet_bulb_temperature(c(10, 20, 30, 40), 50)) > 0))

  # RH is clamped to Stull's 5-99 % validity window
  expect_equal(wet_bulb_temperature(30, 0), wet_bulb_temperature(30, 5))
  expect_equal(wet_bulb_temperature(30, 100), wet_bulb_temperature(30, 99))
})

test_that("wet_bulb_from_dewpoint composes RH and Stull", {
  rh <- relative_humidity_from_dewpoint(30, 22)
  expect_equal(wet_bulb_from_dewpoint(30, 22), wet_bulb_temperature(30, rh))
  expect_true(wet_bulb_from_dewpoint(30, 22) > 22)
  expect_true(wet_bulb_from_dewpoint(30, 22) < 30)
})

test_that("heat_index matches the NWS Rothfusz regression", {
  # 90 F, 70 % RH -> 106 F (NWS heat index chart)
  expect_equal(heat_index(f_to_c(90), 70), f_to_c(106), tolerance = 0.01)
  # 100 F, 40 % RH -> 109 F
  expect_equal(heat_index(f_to_c(100), 40), f_to_c(109), tolerance = 0.01)
  # 86 F, 90 % RH -> 105 F
  expect_equal(heat_index(f_to_c(86), 90), f_to_c(105), tolerance = 0.015)
})

test_that("heat_index uses Steadman's simple formula below 80 F", {
  t_f <- 70
  rh <- 50
  simple_f <- 0.5 * (t_f + 61 + (t_f - 68) * 1.2 + rh * 0.094)
  expect_equal(heat_index(f_to_c(t_f), rh), f_to_c(simple_f))
  # Close to air temperature in mild conditions
  expect_lt(abs(heat_index(20, 50) - 20), 1)
})

test_that("heat_index applies low- and high-humidity adjustments", {
  t_f <- 95
  rh <- 10
  base <- -42.379 + 2.04901523 * t_f + 10.14333127 * rh -
    0.22475541 * t_f * rh - 0.00683783 * t_f^2 - 0.05481717 * rh^2 +
    0.00122874 * t_f^2 * rh + 0.00085282 * t_f * rh^2 -
    0.00000199 * t_f^2 * rh^2
  adj <- -((13 - rh) / 4) * sqrt((17 - abs(t_f - 95)) / 17)
  expect_equal(heat_index(f_to_c(t_f), rh), f_to_c(base + adj))

  t_f <- 84
  rh <- 90
  base <- -42.379 + 2.04901523 * t_f + 10.14333127 * rh -
    0.22475541 * t_f * rh - 0.00683783 * t_f^2 - 0.05481717 * rh^2 +
    0.00122874 * t_f^2 * rh + 0.00085282 * t_f * rh^2 -
    0.00000199 * t_f^2 * rh^2
  adj <- ((rh - 85) / 10) * ((87 - t_f) / 5)
  expect_equal(heat_index(f_to_c(t_f), rh), f_to_c(base + adj))
})

test_that("heat_index is vectorised, monotone in RH when hot, and propagates NA", {
  hi <- heat_index(c(30, 35, 40), c(40, 60, 80))
  expect_length(hi, 3)
  expect_true(all(diff(heat_index(35, c(20, 40, 60, 80))) > 0))
  expect_true(heat_index(40, 60) > 40)
  expect_true(is.na(heat_index(NA_real_, 50)))
  expect_true(is.na(heat_index(35, NA_real_)))
})

test_that("heat_index_from_dewpoint composes RH and heat index", {
  rh <- relative_humidity_from_dewpoint(35, 25)
  expect_equal(heat_index_from_dewpoint(35, 25), heat_index(35, rh))
})

test_that("wbgt_simple follows the BoM closed form", {
  e <- vapor_pressure_from_dewpoint(25)
  expect_equal(wbgt_simple(35, 25), 0.567 * 35 + 0.393 * e + 3.94)
  expect_equal(wbgt_simple(35, 25), 36.23, tolerance = 1e-3)
  expect_true(wbgt_simple(35, 25) > wbgt_simple(35, 15))
  expect_true(wbgt_simple(35, 20) > wbgt_simple(30, 20))
  expect_equal(wbgt_from_dewpoint(c(30, 35), c(20, 25)), wbgt_simple(c(30, 35), c(20, 25)))
})

test_that("wbgt_shade is the ISO 7243 indoor weighting", {
  expect_equal(wbgt_shade(35, 27), 0.7 * 27 + 0.3 * 35)
  expect_equal(wbgt_shade(30, 30), 30)
  expect_equal(wbgt_shade(c(30, 40), c(20, 25)), c(23, 29.5))
})

test_that("humidex follows the Environment Canada formula", {
  # ECCC glossary: e = 6.11 exp(5417.7530 (1/273.15 - 1/Td[K])), humidex = T + 0.5555 (e - 10)
  td <- c(5, 15, 25)
  e <- 6.11 * exp(5417.7530 * (1 / 273.15 - 1 / (td + 273.15)))
  expect_equal(humidex(30, td), 30 + 0.5555 * (e - 10))
  expect_true(all(diff(humidex(30, c(10, 15, 20, 25))) > 0))
})

test_that("mean_radiant_temperature returns air temp without radiation", {
  expect_equal(mean_radiant_temperature(30), 30)
  expect_equal(mean_radiant_temperature(c(10, 20)), c(10, 20))
  expect_equal(mean_radiant_temperature(30, solar_radiation = 0), 30, tolerance = 1e-10)
})

test_that("mean_radiant_temperature increases with solar load", {
  sigma <- 5.670374419e-8
  ta_k <- 303.15
  expected <- (ta_k^4 + 0.7 * 0.25 * 800 / (0.97 * sigma))^0.25 - 273.15
  expect_equal(mean_radiant_temperature(30, 800, 2), expected)
  # wind speed does not affect the radiant estimate
  expect_equal(mean_radiant_temperature(30, 800, 2), mean_radiant_temperature(30, 800, 10))
  tm <- mean_radiant_temperature(30, c(0, 200, 400, 800))
  expect_true(all(diff(tm) > 0))
  expect_true(tm[4] > 45 && tm[4] < 60)
})

test_that("utci reproduces Broede (2012) operational values", {
  # Neutral reference: Ta = 20, va = 0.5, Tmrt = Ta, RH 50 % -> UTCI ~ 20
  td <- 20 - (100 - 50) / 5 # approx dewpoint giving ~50 % RH
  expect_equal(utci(20, wind_speed = 0.5, dewpoint_c = td), 20, tolerance = 0.05)
  expect_equal(utci(30, wind_speed = 2, dewpoint_c = 20), 30.04, tolerance = 1e-3)
})

test_that("utci responds physically to wind, radiation and humidity", {
  # More wind -> cooler in warm conditions
  expect_true(utci(30, 0.5, 20) > utci(30, 5, 20))
  # Radiation load -> warmer
  expect_true(utci(30, 2, 20, tmrt = 50) > utci(30, 2, 20, tmrt = 30))
  # tmrt equal to air temp is identical to no tmrt
  expect_equal(utci(30, 2, 20, tmrt = 30), utci(30, 2, 20))
  # More humid -> warmer when hot
  expect_true(utci(35, 1, 28) > utci(35, 1, 10))
})

test_that("utci clamps wind speed and delta-Tmrt to valid ranges", {
  expect_equal(utci(25, 0, 15), utci(25, 0.5, 15))
  expect_equal(utci(25, 40, 15), utci(25, 17, 15))
  expect_equal(utci(25, 2, 15, tmrt = 200), utci(25, 2, 15, tmrt = 25 + 70))
  expect_equal(utci(25, 2, 15, tmrt = -100), utci(25, 2, 15, tmrt = 25 - 30))
})

test_that("utci is vectorised", {
  v <- utci(c(25, 30, 35), c(1, 2, 3), c(15, 20, 25))
  expect_length(v, 3)
  expect_equal(v[2], utci(30, 2, 20))
})

test_that("utci_sparse agrees with Broede utci near reference conditions", {
  ref <- utci_sparse(20, tmrt = 20, wind_speed = 0.5, rh = 50)
  expect_equal(ref, 20, tolerance = 0.05)

  for (cond in list(c(25, 1, 60), c(30, 2, 50), c(35, 1, 40))) {
    ta <- cond[1]
    va <- cond[2]
    rh <- cond[3]
    # dewpoint giving the requested RH (Magnus inverse)
    g <- log(rh / 100) + 17.625 * ta / (243.04 + ta)
    td <- 243.04 * g / (17.625 - g)
    expect_equal(relative_humidity_from_dewpoint(ta, td), rh, tolerance = 1e-8)
    expect_lt(abs(utci_sparse(ta, ta, va, rh) - utci(ta, va, td)), 1.5)
  }
})

test_that("utci_sparse behaves monotonically and clamps inputs", {
  expect_true(utci_sparse(30, 50, 2, 60) > utci_sparse(30, 30, 2, 60))
  expect_true(utci_sparse(30, 30, 0.5, 60) > utci_sparse(30, 30, 8, 60))
  expect_equal(utci_sparse(30, 30, 0, 60), utci_sparse(30, 30, 0.5, 60))
  expect_equal(utci_sparse(30, 30, 50, 60), utci_sparse(30, 30, 30.3, 60))
  expect_equal(utci_sparse(30, 30, 2, 0), utci_sparse(30, 30, 2, 5))
  expect_equal(utci_sparse(30, 30, 2, 120), utci_sparse(30, 30, 2, 100))
  expect_length(utci_sparse(c(20, 30), c(25, 35), c(1, 2), c(50, 60)), 2)
})

test_that("utci_category uses the standard UTCI stress bands", {
  cats <- utci_category(c(-50, -40, -27, -13, 0, 9, 26, 32, 38, 46))
  expect_s3_class(cats, "factor")
  expect_equal(nlevels(cats), 10)
  # Each boundary value starts a new class (left-closed intervals)
  expect_equal(as.integer(cats), 1:10)
  expect_equal(as.character(cats[1]), "Extreme cold stress")
  expect_equal(as.character(cats[6]), "No thermal stress")
  expect_equal(as.character(cats[10]), "Extreme heat stress")
  # Just below each boundary falls in the class below
  below <- utci_category(c(-40, -27, -13, 0, 9, 26, 32, 38, 46) - 0.01)
  expect_equal(as.integer(below), 1:9)
  expect_true(is.na(utci_category(NA_real_)))
})

test_that("wbgt_risk_category uses NWS 78/82/85/88 F flag thresholds", {
  thresholds <- f_to_c(c(78, 82, 85, 88))
  r <- wbgt_risk_category(c(20, thresholds + 0.001))
  expect_equal(as.character(r), c("Low", "Moderate", "High", "Very high", "Extreme"))
  r_below <- wbgt_risk_category(thresholds - 0.01)
  expect_equal(as.character(r_below), c("Low", "Moderate", "High", "Very high"))
  expect_equal(levels(r), c("Low", "Moderate", "High", "Very high", "Extreme"))
  expect_true(is.na(wbgt_risk_category(NA_real_)))
})

test_that("heat_index_risk_category uses NWS 80/90/103/124 F thresholds", {
  thresholds <- f_to_c(c(80, 90, 103, 124))
  r <- heat_index_risk_category(c(20, thresholds + 0.001))
  expect_equal(
    as.character(r),
    c("Normal", "Caution", "Extreme Caution", "Danger", "Extreme Danger")
  )
  r_below <- heat_index_risk_category(thresholds - 0.01)
  expect_equal(as.character(r_below), c("Normal", "Caution", "Extreme Caution", "Danger"))
  # 106 F from the NWS example is "Danger"
  expect_equal(as.character(heat_index_risk_category(heat_index(f_to_c(90), 70))), "Danger")
})

test_that("calc_heat_indices returns a consistent data frame", {
  out <- calc_heat_indices(c(30, 35, 40), c(20, 25, 28))
  expect_s3_class(out, "data.frame")
  expect_equal(nrow(out), 3)
  expect_named(out, c("temp_c", "dewpoint_c", "rh", "wet_bulb", "heat_index", "wbgt", "humidex"))
  rh <- relative_humidity_from_dewpoint(35, 25)
  expect_equal(out$rh[2], round(rh, 1))
  expect_equal(out$wet_bulb[2], round(wet_bulb_temperature(35, rh), 2))
  expect_equal(out$heat_index[2], round(heat_index(35, rh), 2))
  expect_equal(out$wbgt[2], round(wbgt_simple(35, 25), 2))
  expect_equal(out$humidex[2], round(humidex(35, 25), 2))
  expect_true(all(out$wet_bulb < out$temp_c))
  expect_true(all(out$wet_bulb > out$dewpoint_c))
})

fake_era5 <- function(variables) {
  vals <- c(
    "2m_temperature" = 35,
    "2m_dewpoint_temperature" = 25,
    "10m_u_component_of_wind" = 3,
    "10m_v_component_of_wind" = 4,
    "surface_solar_radiation_downwards" = 500 * 86400
  )
  grid <- expand.grid(
    datetime = as.POSIXct(c("2023-05-01 12:00", "2023-05-02 12:00"), tz = "UTC"),
    latitude = c(20, 21),
    longitude = c(77, 78)
  )
  grid$value <- unname(vals[variables]) + as.numeric(as.Date(grid$datetime) - as.Date("2023-05-01"))
  grid
}

make_era5_mock <- function(calls) {
  function(request_id, variables, ...) {
    calls$ids <- c(calls$ids, request_id)
    calls$vars <- c(calls$vars, variables)
    calls$args[[length(calls$args) + 1]] <- list(...)
    fake_era5(variables)
  }
}

test_that("GetERA5DailyClimate validates region and variables", {
  expect_error(
    GetERA5DailyClimate("x", "2023-05-01", "2023-05-02"),
    "json_file or the bounding box"
  )
  expect_error(
    GetERA5DailyClimate("x", "2023-05-01", "2023-05-02", north = 1, south = 0, east = 1),
    "json_file or the bounding box"
  )
  expect_error(
    GetERA5DailyClimate("x", "2023-05-01", "2023-05-02",
      variables = c("temperature", "pressure"),
      north = 1, south = 0, east = 1, west = 0
    ),
    "Incorrect variables: pressure"
  )
  expect_error(GetERA5DailyHeatIndexData("x", "2023-05-01", "2023-05-02"), "bounding box")
})

test_that("GetERA5DailyClimate assembles temperature, humidity and wet bulb", {
  calls <- new.env()
  local_mocked_bindings(
    era5ify_bbox = make_era5_mock(calls),
    era5ify_geojson = function(...) stop("should not be called")
  )
  out <- GetERA5DailyClimate("req", "2023-05-01", "2023-05-02",
    variables = c("wet_bulb"),
    north = 21, south = 20, east = 78, west = 77
  )
  expect_equal(calls$ids, c("req_temp", "req_dewpoint"))
  expect_equal(calls$vars, c("2m_temperature", "2m_dewpoint_temperature"))
  expect_equal(calls$args[[1]]$frequency, "daily")
  expect_true(calls$args[[1]]$convert_units)
  expect_equal(nrow(out), 8)
  expect_true(all(c("date", "latitude", "longitude", "temp_c", "dewpoint_c", "rh", "wet_bulb") %in% names(out)))
  expect_s3_class(out$date, "Date")
  expect_equal(out$rh, relative_humidity_from_dewpoint(out$temp_c, out$dewpoint_c))
  expect_equal(out$wet_bulb, wet_bulb_temperature(out$temp_c, out$rh))
})

test_that("GetERA5DailyClimate uses geojson path and computes wind and solar", {
  calls <- new.env()
  local_mocked_bindings(
    era5ify_geojson = make_era5_mock(calls),
    era5ify_bbox = function(...) stop("should not be called")
  )
  out <- GetERA5DailyClimate("g", "2023-05-01", "2023-05-02",
    variables = c("wind", "solar"), json_file = "region.geojson"
  )
  expect_equal(calls$ids, c("g_wind_u", "g_wind_v", "g_solar"))
  expect_equal(calls$args[[1]]$json_file, "region.geojson")
  expect_named(out, c("date", "latitude", "longitude", "wind_speed", "solar_radiation"))
  day1 <- out[out$date == as.Date("2023-05-01"), ]
  expect_equal(unique(day1$wind_speed), 5) # sqrt(3^2 + 4^2)

  out_solar <- GetERA5DailyClimate("g", "2023-05-01", "2023-05-02",
    variables = "solar", json_file = "region.geojson"
  )
  expect_named(out_solar, c("date", "latitude", "longitude", "solar_radiation"))
})

test_that("single-variable ERA5 wrappers request the right variables", {
  calls <- new.env()
  local_mocked_bindings(era5ify_bbox = make_era5_mock(calls))
  bb <- list(north = 21, south = 20, east = 78, west = 77)

  t <- do.call(GetERA5DailyTemperature, c(list("a", "2023-05-01", "2023-05-02"), bb))
  expect_named(t, c("date", "latitude", "longitude", "temp_c"))

  h <- do.call(get_era5_daily_humidity, c(list("a", "2023-05-01", "2023-05-02"), bb))
  expect_true(all(c("dewpoint_c", "rh") %in% names(h)))
  expect_false("wet_bulb" %in% names(h))

  w <- do.call(GetERA5DailyWetBulb, c(list("a", "2023-05-01", "2023-05-02"), bb))
  expect_true("wet_bulb" %in% names(w))

  wi <- do.call(GetERA5DailyWind, c(list("a", "2023-05-01", "2023-05-02"), bb))
  expect_named(wi, c("date", "latitude", "longitude", "wind_speed"))

  expect_identical(get_era5_daily_climate, GetERA5DailyClimate)
  expect_identical(get_era5_daily_temperature, GetERA5DailyTemperature)
  expect_identical(get_era5_daily_wet_bulb, GetERA5DailyWetBulb)
  expect_identical(get_era5_daily_wind, GetERA5DailyWind)
})

test_that("GetERA5DailyHeatIndexData derives all indices and categories", {
  calls <- new.env()
  local_mocked_bindings(era5ify_bbox = make_era5_mock(calls))
  out <- GetERA5DailyHeatIndexData("hd", "2023-05-01", "2023-05-02",
    north = 21, south = 20, east = 78, west = 77
  )
  expect_equal(nrow(out), 8)
  expect_true(all(c(
    "temp_c", "dewpoint_c", "wind_speed", "rh", "wet_bulb", "heat_index",
    "wbgt", "utci", "humidex", "wbgt_risk", "heat_index_risk", "utci_stress"
  ) %in% names(out)))
  expect_false("solar_radiation" %in% names(out))
  r <- out[1, ]
  expect_equal(r$heat_index, heat_index(r$temp_c, r$rh))
  expect_equal(r$wbgt, wbgt_simple(r$temp_c, r$dewpoint_c))
  expect_equal(r$utci, utci(r$temp_c, r$wind_speed, r$dewpoint_c))
  expect_equal(r$humidex, humidex(r$temp_c, r$dewpoint_c))
  expect_equal(as.character(r$wbgt_risk), as.character(wbgt_risk_category(r$wbgt)))
  expect_s3_class(out$utci_stress, "factor")
  expect_false(any(c("solar_u", "solar") %in% calls$ids))
})

test_that("GetERA5DailyHeatIndexData with solar load uses radiant temperature", {
  calls <- new.env()
  local_mocked_bindings(era5ify_bbox = make_era5_mock(calls))
  out <- GetERA5DailyHeatData("hs", "2023-05-01", "2023-05-02",
    north = 21, south = 20, east = 78, west = 77, solar_load = TRUE
  )
  expect_true("hs_solar" %in% calls$ids)
  expect_true("solar_radiation" %in% names(out))
  expect_false(any(c("tmrt", "solar_radiation_wm2") %in% names(out)))
  r <- out[1, ]
  tmrt <- mean_radiant_temperature(r$temp_c, r$solar_radiation / 86400)
  expect_equal(r$utci, utci(r$temp_c, r$wind_speed, r$dewpoint_c, tmrt = tmrt))
  # Solar load raises UTCI relative to shade
  expect_true(r$utci > utci(r$temp_c, r$wind_speed, r$dewpoint_c))
  expect_identical(get_era5_daily_heat_index_data, GetERA5DailyHeatIndexData)
  expect_identical(get_era5_daily_heat_data, GetERA5DailyHeatIndexData)
})

test_that("GetERA5MonthlyHeatIndexData averages daily data per grid cell", {
  calls <- new.env()
  local_mocked_bindings(era5ify_bbox = make_era5_mock(calls))
  out <- GetERA5MonthlyHeatIndexData("m",
    year = 2023, month = 12,
    north = 21, south = 20, east = 78, west = 77
  )
  # Date range spans the whole of December
  expect_equal(calls$args[[1]]$start_date, "2023-12-01")
  expect_equal(calls$args[[1]]$end_date, "2023-12-31")
  expect_equal(nrow(out), 4)
  expect_true(all(out$year == 2023 & out$month == 12))
  # The mock values are 35 and 36 on the two days -> mean 35.5
  expect_equal(out$temp_c, rep(35.5, 4))
  expect_true(all(c("wbgt_risk", "heat_index_risk", "utci_stress") %in% names(out)))
  expect_identical(GetERA5MonthlyHeatData, GetERA5MonthlyHeatIndexData)
  expect_identical(get_era5_monthly_heat_data, GetERA5MonthlyHeatIndexData)
  expect_identical(get_era5_monthly_heat_index_data, GetERA5MonthlyHeatIndexData)
})

test_that("GetERA5MonthlyHeatIndexData computes correct month boundaries", {
  seen <- new.env()
  local_mocked_bindings(
    era5ify_bbox = function(request_id, variables, start_date, end_date, ...) {
      seen$start <- start_date
      seen$end <- end_date
      fake_era5(variables)
    }
  )
  GetERA5MonthlyHeatIndexData("m", 2024, 2, north = 21, south = 20, east = 78, west = 77, solar_load = TRUE)
  expect_equal(seen$start, "2024-02-01")
  expect_equal(seen$end, "2024-02-29")
  GetERA5MonthlyHeatIndexData("m", 2023, 12, north = 21, south = 20, east = 78, west = 77)
  expect_equal(seen$start, "2023-12-01")
  expect_equal(seen$end, "2023-12-31")
})

test_that("heat_index gives no NaN warning outside the dry-air adjustment range", {
  # 5 degC and 45 degC with dry air: the adjustment does not apply to these values
  expect_no_warning(hi <- heat_index(c(5, 45, 35), c(10, 10, 10)))
  expect_false(anyNA(hi))
})

test_that("heat_index applies the dry-air adjustment between 80 and 112 degF", {
  # 35 degC = 95 degF, RH 5%: adjustment = -((13 - 5) / 4) * sqrt(17 / 17) = -2 degF
  t_f <- 95
  rh <- 5
  hi_f <- -42.379 + 2.04901523 * t_f + 10.14333127 * rh - 0.22475541 * t_f * rh -
    0.00683783 * t_f^2 - 0.05481717 * rh^2 + 0.00122874 * t_f^2 * rh +
    0.00085282 * t_f * rh^2 - 0.00000199 * t_f^2 * rh^2 - 2
  expect_equal(heat_index(35, 5), (hi_f - 32) * 5 / 9)
})
