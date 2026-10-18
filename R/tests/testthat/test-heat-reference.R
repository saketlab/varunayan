# Heat stress formulas checked against independent physics: the Goff-Gratch
# saturation vapour pressure over water (WMO 1988) and a psychrometric
# wet-bulb solve. These are oracles, so tolerances state each approximation's
# known error and are not fitted to the package output.

# Goff-Gratch (1946) over water, WMO Technical Regulations (1988), hPa.
goff_gratch <- function(t_c) {
  tk <- t_c + 273.15
  ts <- 373.16
  10^(-7.90298 * (ts / tk - 1) + 5.02808 * log10(ts / tk) -
    1.3816e-7 * (10^(11.344 * (1 - tk / ts)) - 1) +
    8.1328e-3 * (10^(-3.49149 * (ts / tk - 1)) - 1) + log10(1013.246))
}

# Psychrometric equation e = es(Tw) - A p (T - Tw), A = 6.53e-4 (1 + 0.000944 Tw)
# per K for a ventilated psychrometer (WMO-No. 8, Annex 4.B), solved for Tw.
psychrometric_wet_bulb <- function(t_c, rh, p = 1013.25) {
  e <- rh / 100 * goff_gratch(t_c)
  stats::uniroot(
    function(tw) goff_gratch(tw) - 6.53e-4 * (1 + 0.000944 * tw) * p * (t_c - tw) - e,
    c(-60, t_c),
    tol = 1e-8
  )$root
}

# ---- saturation vapour pressure -------------------------------------------

test_that("vapor_pressure_from_dewpoint (Bolton 1980) tracks Goff-Gratch", {
  t <- seq(-30, 45, by = 0.5)
  rel <- vapor_pressure_from_dewpoint(t) / goff_gratch(t) - 1
  expect_lt(max(abs(rel)), 0.005)
  warm <- t >= 0 & t <= 35
  expect_lt(max(abs(rel[warm])), 0.002)
})

test_that("the UTCI saturation routine tracks Goff-Gratch in kPa", {
  t <- seq(-30, 45, by = 0.5)
  rel <- varunayan:::.utci_saturation_kpa(t) * 10 / goff_gratch(t) - 1
  expect_lt(max(abs(rel)), 0.004)
  expect_lt(max(abs(rel[t >= 0])), 0.002)
  # 100 C boils at one standard atmosphere
  expect_equal(varunayan:::.utci_saturation_kpa(100), 101.325, tolerance = 2e-3)
})

test_that("the Liljegren saturation routine tracks Goff-Gratch", {
  t <- seq(-30, 45, by = 0.5)
  rel <- varunayan:::.lj_esat(t + 273.15) / goff_gratch(t) - 1
  expect_lt(max(abs(rel)), 0.01)
})

test_that("saturation vapour pressure is strictly increasing and positive", {
  t <- seq(-40, 50, by = 0.1)
  for (es in list(vapor_pressure_from_dewpoint(t), varunayan:::.utci_saturation_kpa(t))) {
    expect_true(all(es > 0))
    expect_true(all(diff(es) > 0))
  }
})

# ---- relative humidity ----------------------------------------------------

test_that("relative_humidity_from_dewpoint matches the Goff-Gratch ratio", {
  g <- expand.grid(t = seq(-20, 50, by = 1), td = seq(-40, 50, by = 1))
  g <- g[g$td <= g$t, ]
  truth <- 100 * goff_gratch(g$td) / goff_gratch(g$t)
  rh <- relative_humidity_from_dewpoint(g$t, g$td)
  # Alduchov & Eskridge (1996) Magnus constants: < 0.2 %RH absolute over this range
  expect_lt(max(abs(rh - truth)), 0.2)
})

test_that("relative humidity is 100 at saturation, falls with T, rises with Td", {
  t <- seq(-20, 50, by = 5)
  expect_equal(relative_humidity_from_dewpoint(t, t), rep(100, length(t)))
  expect_true(all(diff(relative_humidity_from_dewpoint(seq(10, 45, 1), 10)) < 0))
  expect_true(all(diff(relative_humidity_from_dewpoint(35, seq(-10, 35, 1))) > 0))
  # supersaturated input is capped, very dry input stays positive
  expect_equal(relative_humidity_from_dewpoint(c(20, 30), c(25, 40)), c(100, 100))
  expect_gt(relative_humidity_from_dewpoint(45, -40), 0)
})

test_that("relative humidity depends only on T - Td at fixed T (vectorised)", {
  t <- rep(c(15, 25, 35), each = 4)
  td <- t - rep(c(0, 2, 8, 20), 3)
  expect_equal(
    relative_humidity_from_dewpoint(t, td),
    mapply(relative_humidity_from_dewpoint, t, td)
  )
})

# ---- wet bulb (Stull 2011) ------------------------------------------------

test_that("Stull wet bulb is within its published error of a psychrometric solve", {
  g <- expand.grid(t = seq(0, 50, by = 2), rh = seq(10, 99, by = 3))
  ref <- mapply(psychrometric_wet_bulb, g$t, g$rh)
  err <- wet_bulb_temperature(g$t, g$rh) - ref
  # Stull (2011): errors of -1 to +0.65 C against his reference; the reference
  # here uses a different psychrometer constant, so allow 1 C either side
  expect_lt(max(abs(err)), 1)
  core <- g$t >= 10 & g$t <= 40 & g$rh >= 20
  expect_lt(max(abs(err[core])), 0.8)
  expect_lt(abs(mean(err[core])), 0.3)
})

test_that("Stull wet bulb lies between dewpoint and air temperature", {
  g <- expand.grid(t = seq(5, 48, by = 1), dep = c(1, 3, 6, 10, 15))
  g$td <- g$t - g$dep
  rh <- relative_humidity_from_dewpoint(g$t, g$td)
  g <- g[rh >= 20, ]
  tw <- wet_bulb_from_dewpoint(g$t, g$td)
  # Stull's error lets it dip slightly below Td in near-saturated air
  expect_true(all(tw >= g$td - 0.7))
  expect_true(all(tw <= g$t + 0.1))
})

test_that("wet bulb is monotone in T and RH in warm air", {
  # Stull (2011) warns the fit degrades in cold, dry air, where it is not monotone
  rh <- seq(5, 99, by = 1)
  for (t in c(10, 20, 35, 50)) expect_true(all(diff(wet_bulb_temperature(t, rh)) > 0))
  t <- seq(0, 50, by = 0.5)
  for (r in c(5, 30, 60, 99)) expect_true(all(diff(wet_bulb_temperature(t, r)) > 0))
})

test_that("the 35 C wet bulb survivability limit needs very humid heat", {
  # Sherwood & Huber (2010): Tw = 35 C limit; 35 C at saturation reaches it
  expect_equal(wet_bulb_temperature(35, 99), 35, tolerance = 0.01)
  expect_lt(wet_bulb_temperature(45, 40), 35)
  expect_gt(wet_bulb_temperature(40, 75), 35)
})

test_that("wet bulb propagates NA and recycles vectors", {
  expect_equal(is.na(wet_bulb_temperature(c(30, NA, 30), c(50, 50, NA))), c(FALSE, TRUE, TRUE))
  expect_length(wet_bulb_temperature(30, c(20, 40, 60)), 3)
})

# ---- heat index -----------------------------------------------------------

# NWS Weather Prediction Center algorithm, written out per element.
nws_heat_index_f <- function(t, rh) {
  simple <- 0.5 * (t + 61 + (t - 68) * 1.2 + rh * 0.094)
  if ((simple + t) / 2 < 80) {
    return(simple)
  }
  hi <- -42.379 + 2.04901523 * t + 10.14333127 * rh - 0.22475541 * t * rh -
    0.00683783 * t^2 - 0.05481717 * rh^2 + 0.00122874 * t^2 * rh +
    0.00085282 * t * rh^2 - 0.00000199 * t^2 * rh^2
  if (rh < 13 && t >= 80 && t <= 112) {
    hi <- hi - ((13 - rh) / 4) * sqrt((17 - abs(t - 95)) / 17)
  } else if (rh > 85 && t >= 80 && t <= 87) {
    hi <- hi + ((rh - 85) / 10) * ((87 - t) / 5)
  }
  hi
}

test_that("heat_index equals the NWS algorithm across 40-120 F and 0-100 % RH", {
  g <- expand.grid(t = seq(40, 120, by = 1), rh = seq(0, 100, by = 1))
  ref <- mapply(nws_heat_index_f, g$t, g$rh)
  expect_equal(heat_index(f_to_c(g$t), g$rh) * 9 / 5 + 32, ref, tolerance = 1e-10)
})

test_that("heat_index vectorises without mixing branches between elements", {
  set.seed(1)
  t <- runif(500, 5, 50)
  rh <- runif(500, 0, 100)
  expect_equal(heat_index(t, rh), mapply(heat_index, t, rh))
  # shuffling the inputs shuffles the outputs
  o <- sample(500)
  expect_equal(heat_index(t[o], rh[o]), heat_index(t, rh)[o])
})

test_that("heat_index exceeds air temperature in humid heat and is close to it when mild", {
  # the NWS chart itself has HI below T at 40 % RH under 90 F
  g <- expand.grid(t = f_to_c(seq(85, 110, 1)), rh = seq(50, 100, 5))
  expect_true(all(heat_index(g$t, g$rh) > g$t))
  expect_true(all(diff(heat_index(35, seq(20, 100, 5))) > 0))
  expect_lt(max(abs(heat_index(seq(10, 24, 1), 50) - seq(10, 24, 1))), 2)
})

test_that("heat_index_from_dewpoint is heat_index at the Magnus RH for many points", {
  g <- expand.grid(t = seq(20, 46, 2), td = seq(0, 30, 3))
  g <- g[g$td <= g$t, ]
  expect_equal(
    heat_index_from_dewpoint(g$t, g$td),
    heat_index(g$t, relative_humidity_from_dewpoint(g$t, g$td))
  )
})

# ---- humidex --------------------------------------------------------------

# Humidex vapour pressure (hPa), with the reference temperature t0 in K.
humidex_e <- function(td, t0 = 273.15) 6.11 * exp(5417.7530 * (1 / t0 - 1 / (273.15 + td)))

test_that("humidex agrees with Masterton & Richardson's 273.16 K form", {
  # The original uses 1/273.16 in the exponent; the package uses 1/273.15.
  td <- seq(-10, 35, by = 0.5)
  orig <- 30 + 0.5555 * (humidex_e(td, 273.16) - 10)
  expect_lt(max(abs(humidex(30, td) - orig)), 0.03)
})

test_that("humidex equals T where vapour pressure is 10 hPa and rises with T and Td", {
  td10 <- stats::uniroot(function(td) humidex_e(td) - 10, c(0, 20))$root
  expect_equal(humidex(c(20, 30, 40), td10), c(20, 30, 40), tolerance = 1e-8)
  expect_true(all(humidex(30, c(10, 20, 25)) > 30))
  expect_true(all(humidex(30, c(-10, 0, 5)) < 30))
  expect_equal(diff(humidex(c(25, 26, 27), 15)), c(1, 1))
  expect_true(all(diff(humidex(32, seq(-5, 30, 1))) > 0))
})

# ---- WBGT -----------------------------------------------------------------

test_that("wbgt_simple is linear: 0.567 per C of air, 0.393 per hPa of vapour", {
  expect_equal(diff(wbgt_simple(c(30, 31, 32), 20)), c(0.567, 0.567))
  e1 <- vapor_pressure_from_dewpoint(15)
  e2 <- vapor_pressure_from_dewpoint(25)
  expect_equal(wbgt_simple(35, 25) - wbgt_simple(35, 15), 0.393 * (e2 - e1))
})

test_that("wbgt_shade lies between wet bulb and air temperature", {
  g <- expand.grid(t = seq(20, 45, 1), rh = seq(10, 95, 5))
  tw <- wet_bulb_temperature(g$t, g$rh)
  w <- wbgt_shade(g$t, tw)
  expect_true(all(w >= tw - 1e-12 & w <= g$t + 1e-12))
  expect_equal(w - tw, 0.3 * (g$t - tw))
})

test_that("wbgt() dispatches simple by default and checks the method", {
  expect_equal(wbgt(c(30, 40), c(20, 25)), wbgt_simple(c(30, 40), c(20, 25)))
  expect_error(wbgt(30, 20, method = "nope"))
})

# ---- Liljegren outdoor WBGT -----------------------------------------------

lj_noon <- as.POSIXct("2024-05-20 06:30:00", tz = "UTC") # 12:00 IST
lj_night <- as.POSIXct("2024-05-20 19:30:00", tz = "UTC") # 01:00 IST
# Jaipur at noon
lj <- function(t, rh, wind, solar, ...) wbgt_liljegren(t, rh, wind, solar, lj_noon, 26.9, 75.8, ...)

test_that("Liljegren WBGT is the ISO 7243 weighting of its components", {
  r <- lj(c(30, 38, 44), c(70, 40, 20), 2, 800, components = TRUE)
  expect_equal(r$wbgt, 0.7 * r$natural_wet_bulb + 0.2 * r$globe + 0.1 * c(30, 38, 44))
})

test_that("Liljegren components obey the physical ordering in sun", {
  g <- expand.grid(t = c(25, 32, 40, 46), rh = c(15, 40, 70, 90), wind = c(0.5, 2, 6))
  r <- lj(g$t, g$rh, g$wind, 850, components = TRUE)
  expect_false(anyNA(r$wbgt))
  # sunlit globe is hotter than the air
  expect_true(all(r$globe > g$t))
  # psychrometric wet bulb sits at or below air temperature
  expect_true(all(r$wet_bulb <= g$t + 1e-6))
  # a sunlit natural wet bulb warms above the shaded psychrometric one
  expect_true(all(r$natural_wet_bulb >= r$wet_bulb - 1e-6))
})

test_that("Liljegren psychrometric wet bulb agrees with the psychrometric solve", {
  g <- expand.grid(t = c(20, 30, 40), rh = c(20, 50, 80))
  r <- wbgt_liljegren(g$t, g$rh, 3, 0, lj_night, 26.9, 75.8, wind_height = 2, components = TRUE)
  ref <- mapply(psychrometric_wet_bulb, g$t, g$rh)
  expect_lt(max(abs(r$wet_bulb - ref)), 1)
})

test_that("Liljegren WBGT rises with sun and humidity and falls with wind in sun", {
  expect_true(all(diff(lj(38, 40, 2, c(0, 200, 400, 600, 800, 1000))) > 0))
  expect_true(all(diff(lj(38, c(10, 30, 50, 70, 90), 2, 800)) > 0))
  expect_true(all(diff(lj(38, 40, c(0.5, 1, 2, 4, 8), 800)) < 0))
})

test_that("Liljegren WBGT without sun is below air temperature in dry air", {
  r <- wbgt_liljegren(c(30, 35, 40), 30, 2, 0, lj_night, 26.9, 75.8)
  expect_true(all(r < c(30, 35, 40)))
})

test_that("Liljegren WBGT vectorises over location and pressure", {
  r <- wbgt_liljegren(38, 40, 2, 800, lj_noon, lat = c(10, 20, 30), lon = 75.8)
  expect_length(r, 3)
  expect_equal(r[2], wbgt_liljegren(38, 40, 2, 800, lj_noon, 20, 75.8))
  p <- lj(38, 40, 2, 800, pressure = c(1013, 850))
  expect_length(p, 2)
})

test_that("Liljegren with wind at 2 m does no height scaling", {
  r <- lj(35, 40, c(1, 3), 600, wind_height = 2, components = TRUE)
  expect_equal(r$wind_2m, c(1, 3))
  r10 <- lj(35, 40, 3, 600, wind_height = 10, components = TRUE)
  expect_lt(r10$wind_2m, 3)
})

# ---- UTCI -----------------------------------------------------------------

test_that("utci recovers air temperature in the UTCI reference environment", {
  # Reference: Tmrt = Ta, 0.5 m/s at 10 m, 50 % RH capped at 20 hPa vapour.
  # Over the comfort range the polynomial offset stays within a couple of degrees.
  ta <- seq(0, 30, by = 2)
  rh <- pmin(50, 2000 / vapor_pressure_from_dewpoint(ta))
  expect_lt(max(abs(utci(ta, 0.5, dewpoint_from_rh(ta, rh)) - ta)), 2.5)
  expect_lt(max(abs(utci_sparse(ta, ta, 0.5, 50) - ta)), 2.5)
})

test_that("utci and utci_sparse agree across a broad hot-climate grid", {
  g <- expand.grid(t = c(20, 30, 40, 45), dt = c(0, 15, 30), va = c(0.5, 2, 6), rh = c(20, 50, 80))
  # UTCI is defined for vapour pressure up to 5 kPa
  g <- g[g$rh / 100 * vapor_pressure_from_dewpoint(g$t) <= 50, ]
  u <- utci(g$t, g$va, dewpoint_from_rh(g$t, g$rh), tmrt = g$t + g$dt)
  s <- utci_sparse(g$t, g$t + g$dt, g$va, g$rh)
  # both approximate the same model; the 6th-order polynomial has RMSE ~1 C
  expect_lt(sqrt(mean((u - s)^2)), 1.5)
  expect_lt(max(abs(u - s)), 5)
})

test_that("utci increases with temperature, radiation and humidity in heat", {
  expect_true(all(diff(utci(seq(25, 45, 1), 1, 15)) > 0))
  expect_true(all(diff(utci(35, 1, 20, tmrt = seq(35, 95, 5))) > 0))
  expect_true(all(diff(utci(38, 1, seq(5, 28, 1))) > 0))
  expect_true(all(diff(utci_sparse(seq(25, 45, 1), seq(25, 45, 1), 1, 50)) > 0))
})

test_that("utci propagates NA element-wise", {
  r <- utci(c(30, NA, 30), c(1, 1, NA), c(20, 20, 20))
  expect_equal(is.na(r), c(FALSE, TRUE, TRUE))
})

# ---- categories -----------------------------------------------------------

test_that("WBGT categories switch exactly at 78, 82, 85 and 88 F", {
  edges <- f_to_c(c(78, 82, 85, 88))
  labels <- c("Low", "Moderate", "High", "Very high", "Extreme")
  expect_equal(as.character(wbgt_risk_category(edges)), labels[2:5])
  expect_equal(as.character(wbgt_risk_category(edges - 1e-6)), labels[1:4])
  expect_equal(levels(wbgt_risk_category(30)), labels)
})

test_that("heat index categories switch exactly at 80, 90, 103 and 124 F", {
  edges <- f_to_c(c(80, 90, 103, 124))
  labels <- c("Normal", "Caution", "Extreme Caution", "Danger", "Extreme Danger")
  expect_equal(as.character(heat_index_risk_category(edges)), labels[2:5])
  expect_equal(as.character(heat_index_risk_category(edges - 1e-6)), labels[1:4])
})

test_that("UTCI categories switch exactly at the Blazejczyk et al. (2013) bounds", {
  edges <- c(-40, -27, -13, 0, 9, 26, 32, 38, 46)
  cats <- as.character(utci_category(edges))
  below <- as.character(utci_category(edges - 1e-9))
  expect_equal(cats[-length(cats)], below[-1])
  expect_equal(
    as.character(utci_category(c(-60, 20, 60))),
    c("Extreme cold stress", "No thermal stress", "Extreme heat stress")
  )
  expect_true(is.na(utci_category(NA_real_)))
})

test_that("categories keep NA and length", {
  expect_equal(is.na(wbgt_risk_category(c(20, NA))), c(FALSE, TRUE))
  expect_length(heat_index_risk_category(numeric()), 0)
})

# ---- calc_heat_indices ----------------------------------------------------

test_that("calc_heat_indices equals the individual functions over a grid", {
  g <- expand.grid(t = seq(20, 46, 3), td = seq(5, 30, 5))
  g <- g[g$td <= g$t, ]
  d <- calc_heat_indices(g$t, g$td)
  rh <- relative_humidity_from_dewpoint(g$t, g$td)
  expect_equal(d$rh, round(rh, 1))
  expect_equal(d$wet_bulb, round(wet_bulb_temperature(g$t, rh), 2))
  expect_equal(d$heat_index, round(heat_index(g$t, rh), 2))
  expect_equal(d$wbgt, round(wbgt_simple(g$t, g$td), 2))
  expect_equal(d$humidex, round(humidex(g$t, g$td), 2))
  # indices order sensibly in humid heat
  hot <- d$temp_c >= 32 & d$rh >= 40
  expect_true(all(d$wet_bulb[hot] < d$temp_c[hot]))
  expect_true(all(d$humidex[hot] > d$temp_c[hot]))
})
