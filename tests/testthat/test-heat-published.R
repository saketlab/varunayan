# Heat stress calculations checked against published values and reference code.

fixture <- function(name) {
  utils::read.delim(test_path("fixtures", name), comment.char = "#")
}

test_that("wet bulb reproduces the worked example in Stull (2011)", {
  # Stull (2011) JAMC 50:2267, Eq. (1) example: T = 20 C, RH = 50 % gives Tw = 13.7 C
  expect_equal(round(wet_bulb_temperature(20, 50), 1), 13.7)
})

test_that("heat index matches the NWS heat index chart", {
  # NWS Heat Index chart (weather.gov/safety/heat-index), RH 40-100 % by T 80-110 F.
  chart <- rbind(
    c(80, 81, 83, 85, 88, 91, 94, 97, 101, 105, 109, 114, 119, 124, 130, 136),
    c(80, 82, 84, 87, 89, 93, 96, 100, 104, 109, 114, 119, 124, 130, 137, NA),
    c(81, 83, 85, 88, 91, 95, 99, 103, 108, 113, 118, 124, 131, 137, NA, NA),
    c(81, 84, 86, 89, 93, 97, 101, 106, 112, 117, 124, 130, 137, NA, NA, NA),
    c(82, 84, 88, 91, 95, 100, 105, 110, 116, 123, 129, 137, NA, NA, NA, NA),
    c(82, 85, 89, 93, 98, 103, 108, 114, 121, 128, 136, NA, NA, NA, NA, NA),
    c(83, 86, 90, 95, 100, 105, 112, 119, 126, 134, NA, NA, NA, NA, NA, NA),
    c(84, 88, 92, 97, 103, 109, 116, 124, 132, NA, NA, NA, NA, NA, NA, NA),
    c(84, 89, 94, 100, 106, 113, 121, 129, NA, NA, NA, NA, NA, NA, NA, NA),
    c(85, 90, 96, 102, 110, 117, 126, 135, NA, NA, NA, NA, NA, NA, NA, NA),
    c(86, 91, 98, 105, 113, 122, 131, NA, NA, NA, NA, NA, NA, NA, NA, NA),
    c(86, 93, 100, 108, 117, 127, NA, NA, NA, NA, NA, NA, NA, NA, NA, NA),
    c(87, 95, 103, 112, 121, 132, NA, NA, NA, NA, NA, NA, NA, NA, NA, NA)
  )
  g <- expand.grid(rh = seq(40, 100, 5), t_f = seq(80, 110, 2))
  g$chart <- as.vector(chart)
  g <- g[!is.na(g$chart), ]
  expect_equal(nrow(g), 135)
  hi_f <- heat_index((g$t_f - 32) * 5 / 9, g$rh) * 9 / 5 + 32
  # Rothfusz (1990): regression error +/-1.3 F against Steadman's table; chart is
  # rounded to 1 F. The high-humidity adjustment (RH > 85 %, 80-87 F) is not in the chart.
  adjusted <- g$rh > 85 & g$t_f <= 87
  expect_true(all(abs(hi_f - g$chart)[!adjusted] <= 1.3 + 0.5))
})

test_that("heat index switches to the regression as the NWS algorithm specifies", {
  # WPC heat index equation: use Rothfusz once (simple + T) / 2 >= 80 F.
  rothfusz <- function(t, rh) {
    -42.379 + 2.04901523 * t + 10.14333127 * rh - 0.22475541 * t * rh -
      0.00683783 * t^2 - 0.05481717 * rh^2 + 0.00122874 * t^2 * rh +
      0.00085282 * t * rh^2 - 0.00000199 * t^2 * rh^2
  }
  simple <- function(t, rh) 0.5 * (t + 61 + (t - 68) * 1.2 + rh * 0.094)
  # 78 F, 90 % RH: simple = 79.73, average 78.87 < 80, so the simple value stands
  expect_equal(heat_index((78 - 32) * 5 / 9, 90) * 9 / 5 + 32, simple(78, 90))
  # 79 F, 100 % RH: simple = 81.3, average 80.15, so Rothfusz; below 80 F, no humidity adjustment
  expect_equal(heat_index((79 - 32) * 5 / 9, 100) * 9 / 5 + 32, rothfusz(79, 100))
  # 84 F, 90 % RH: Rothfusz plus the RH > 85 %, 80-87 F term
  expect_equal(heat_index((84 - 32) * 5 / 9, 90) * 9 / 5 + 32, rothfusz(84, 90) + 0.5 * 0.6)
})

test_that("BoM WBGT approximation reproduces the Bureau's Brisbane example", {
  # bom.gov.au/info/thermal_stress: Brisbane January, 29.4 C and 59 % RH,
  # "a WBGT of about 30 C"; e = rh/100 * 6.105 exp(17.27 T / (237.7 + T)).
  e <- 59 / 100 * 6.105 * exp(17.27 * 29.4 / (237.7 + 29.4))
  bom <- 0.567 * 29.4 + 0.393 * e + 3.94
  expect_equal(round(bom), 30)
  # same air from its dewpoint, through the package
  expect_equal(wbgt_simple(29.4, dewpoint_from_rh(29.4, 59)), bom, tolerance = 0.01)
})

test_that("utci reproduces the operational polynomial values of Broede et al. (2012)", {
  d <- fixture("utci_brode2012.tsv")
  expect_equal(nrow(d), 1000)
  ok <- d$va <= 17 # polynomial wind range
  td <- dewpoint_from_rh(d$Ta, d$rH) # utci() maps it back to rH
  u <- utci(d$Ta[ok], d$va[ok], td[ok], tmrt = d$Ta[ok] + d$TrTa[ok])
  # published values are rounded to 0.1 C
  expect_true(all(abs(u - d$UTCI_polynomial[ok]) <= 0.05 + 1e-6))
})

test_that("utci_sparse matches the reference code of Roman et al. (2025)", {
  d <- fixture("utci_brode2012.tsv")
  s <- utci_sparse(d$Ta, d$Ta + d$TrTa, d$va, d$rH)
  expect_equal(s, d$sparse_reference, tolerance = 1e-9)
  # and is closer to the reference UTCI than the 6th-order polynomial
  expect_lt(sqrt(mean((s - d$UTCI)^2)), sqrt(mean((d$UTCI_polynomial - d$UTCI)^2)))
})

test_that("wbgt_liljegren matches the original Liljegren C implementation", {
  d <- fixture("wbgt_liljegren_reference.tsv")
  t <- as.POSIXct(sprintf("%d-%02d-%02d %02d:%02d:00", d$year, d$month, d$day, d$hour, d$minute), tz = "UTC")
  for (g in split(seq_len(nrow(d)), list(d$zspeed, d$urban), drop = TRUE)) {
    r <- wbgt_liljegren(d$tair[g], d$rh[g], d$speed[g], d$solar[g], t[g], d$lat[g], d$lon[g],
      pressure = d$pres[g], wind_height = d$zspeed[g[1]], urban = d$urban[g[1]] == 1,
      delta_t = d$dt[g], components = TRUE
    )
    expect_equal(r[c("wbgt", "globe", "natural_wet_bulb", "wet_bulb")],
      d[g, c("wbgt", "globe", "natural_wet_bulb", "wet_bulb")],
      tolerance = 1e-8, ignore_attr = TRUE
    )
  }
})

test_that("wbgt() dispatches to both methods", {
  expect_equal(wbgt(35, 25), wbgt_simple(35, 25))
  t <- as.POSIXct("2019-05-20 08:30:00", tz = "UTC")
  rh <- 100 * varunayan:::.lj_esat(25 + 273.15) / varunayan:::.lj_esat(35 + 273.15)
  expect_equal(
    wbgt(35, 25, method = "liljegren", wind_speed = 2, solar = 700, datetime = t, lat = 26.9, lon = 75.8),
    wbgt_liljegren(35, rh, 2, 700, t, 26.9, 75.8)
  )
  expect_error(wbgt_liljegren(35, 50, 2, 700, "2019-05-20", 26.9, 75.8), "POSIXct")
})

test_that("NDVI and NDBI follow Tucker (1979) and Zha et al. (2003)", {
  expect_equal(ndvi(0.5, 0.1), (0.5 - 0.1) / (0.5 + 0.1))
  expect_equal(ndbi(0.3, 0.2), (0.3 - 0.2) / (0.3 + 0.2))
  expect_equal(ndvi(c(0.4, 0.1), c(0.1, 0.4)), c(0.6, -0.6))
  skip_if_not_installed("terra")
  r <- terra::rast(nrows = 1, ncols = 2, vals = c(0.4, 0.1))
  expect_equal(terra::values(ndvi(r, r / 4))[, 1], c(0.6, 0.6))
})
