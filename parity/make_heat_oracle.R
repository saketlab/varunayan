# Write heat_oracle.json from the R heat functions; run from the repo root.
devtools::load_all("R", quiet = TRUE)

grid <- expand.grid(temp_c = c(-10, 0, 15, 26.7, 30, 35, 40, 46), rh = c(5, 20, 40, 60, 80, 100))
temp <- grid$temp_c
rh <- grid$rh
dew <- dewpoint_from_relative_humidity(temp, rh)
wet <- wet_bulb_temperature(temp, rh)
hi <- c(20, 26.6, 27, 32, 32.5, 39, 40, 51, 52, 60)
wb <- c(20, 25.6, 26, 27.7, 28, 29.4, 30, 32.2, 33, 35)
uv <- c(-50, -27, -13, 0, 9, 26, 28, 32, 38, 46, 50)

case <- function(name, fn, args, tol = 1e-9) {
  list(name = name, `function` = fn, args = args,
       expected = do.call(fn, args), tol = tol)
}
cases <- list(
  case("heat_rh_from_dewpoint", "relative_humidity_from_dewpoint", list(temp_c = temp, dewpoint_c = dew)),
  case("heat_vapor_pressure", "vapor_pressure_from_dewpoint", list(dewpoint_c = dew)),
  case("heat_wet_bulb", "wet_bulb_temperature", list(temp_c = temp, rh = rh)),
  case("heat_wet_bulb_from_dewpoint", "wet_bulb_from_dewpoint", list(temp_c = temp, dewpoint_c = dew)),
  case("heat_index", "heat_index", list(temp_c = temp, rh = rh)),
  case("heat_index_from_dewpoint", "heat_index_from_dewpoint", list(temp_c = temp, dewpoint_c = dew)),
  case("heat_humidex", "humidex", list(temp_c = temp, dewpoint_c = dew)),
  case("heat_wbgt_simple", "wbgt_simple", list(temp_c = temp, dewpoint_c = dew)),
  case("heat_wbgt_shade", "wbgt_shade", list(temp_c = temp, wet_bulb_c = wet)),
  case("heat_index_risk", "heat_index_risk_category", list(hi = hi)),
  case("heat_wbgt_risk", "wbgt_risk_category", list(wbgt = wb)),
  case("heat_utci_category", "utci_category", list(utci_val = uv)),
  case("heat_utci_shade", "utci", list(temp_c = temp, wind_speed = rep(c(0.5, 2, 6, 12), length.out = length(temp)), dewpoint_c = dew)),
  case("heat_utci_sun", "utci", list(
    temp_c = c(25, 30, 35, 40, 45), wind_speed = c(1, 2, 3, 4, 1),
    dewpoint_c = c(15, 20, 25, 22, 10), tmrt = c(40, 55, 60, 70, 95)
  )),
  case("heat_mrt", "mean_radiant_temperature", list(temp_c = c(20, 30, 38, 45), solar_radiation = c(0, 300, 700, 1000))),
  case("heat_calc_indices", "calc_heat_indices", list(temp_c = c(25, 30, 35, 40, 46), dewpoint_c = c(10, 20, 25, 28, 30))),
  case("heat_utci_sparse", "utci_sparse", list(
    temp_c = c(20, 30, 35, 40), tmrt = c(25, 45, 55, 60),
    wind_speed = c(0.5, 1, 3, 6), rh = c(50, 40, 60, 30)
  ))
)
jsonlite::write_json(cases, "parity/heat_oracle.json", digits = NA, pretty = TRUE, na = "null", auto_unbox = TRUE, dataframe = "columns")
cat("wrote", length(cases), "heat cases\n")
