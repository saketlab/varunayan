# Outdoor WBGT after Liljegren et al. (2008).
#
# Vectorised R translation of wbgt.c (WBGT Version 1.1) by James C. Liljegren,
# translated by Saket Choudhary, IIT Bombay. Changes from the original: loops
# over observations became vectorised iteration; the date is a POSIXct instant
# in UTC; the sun position uses exact elapsed days (the original counts the leap
# day of years after 2000 that are divisible by four from 1 January);
# non-convergence returns NA (the original returns -9999); a zero direct-beam
# fraction drops the direct-beam term, avoiding 0 * Inf at a cosine zenith of zero.
#
# The original notice follows, as its licence requires.
#
#                Copyright (c) 2008, UChicago Argonne, LLC
#                        All Rights Reserved
#
#                         WBGT, Version 1.1
#
#                       James C. Liljegren
#               Decision & Information Sciences Division
#
#                       OPEN SOURCE LICENSE
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.  Software changes,
#    modifications, or derivative works, should be noted with comments and
#    the author and organization's name.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the names of UChicago Argonne, LLC or the Department of Energy
#    nor the names of its contributors may be used to endorse or promote
#    products derived from this software without specific prior written
#    permission.
#
# 4. The software and the end-user documentation included with the
#    redistribution, if any, must include the following acknowledgment:
#
#    "This product includes software produced by UChicago Argonne, LLC
#    under Contract No. DE-AC02-06CH11357 with the Department of Energy."
#
# DISCLAIMER
#
# THE SOFTWARE IS SUPPLIED "AS IS" WITHOUT WARRANTY OF ANY KIND.
#
# NEITHER THE UNITED STATES GOVERNMENT, NOR THE UNITED STATES DEPARTMENT OF
# ENERGY, NOR UCHICAGO ARGONNE, LLC, NOR ANY OF THEIR EMPLOYEES, MAKES ANY
# WARRANTY, EXPRESS OR IMPLIED, OR ASSUMES ANY LEGAL LIABILITY OR
# RESPONSIBILITY FOR THE ACCURACY, COMPLETENESS, OR USEFULNESS OF ANY
# INFORMATION, DATA, APPARATUS, PRODUCT, OR PROCESS DISCLOSED, OR REPRESENTS
# THAT ITS USE WOULD NOT INFRINGE PRIVATELY OWNED RIGHTS.

.LJ <- list(
  solar_const = 1367, stefanb = 5.6696e-8, cp = 1003.5,
  m_air = 28.97, m_h2o = 18.015, r_gas = 8314.34,
  emis_wick = 0.95, alb_wick = 0.4, d_wick = 0.007, l_wick = 0.0254,
  emis_globe = 0.95, alb_globe = 0.05, d_globe = 0.0508,
  emis_sfc = 0.999, alb_sfc = 0.45,
  cza_min = 0.00873, normsolar_max = 0.85, ref_height = 2, min_speed = 0.13,
  convergence = 0.02, max_iter = 500L
)
.LJ$r_air <- .LJ$r_gas / .LJ$m_air
.LJ$ratio <- .LJ$cp * .LJ$m_air / .LJ$m_h2o
.LJ$pr <- .LJ$cp / (.LJ$cp + 1.25 * .LJ$r_air)
.LJ$k_visc <- .LJ$cp + 1.25 * .LJ$r_air # thermal conductivity per unit viscosity
.LJ$tcrit12 <- sqrt(132 * 647.3)
.LJ$diff_coef <- 3.64e-4 * (36.4 * 218)^(1 / 3) * (132 * 647.3)^(5 / 12) *
  sqrt(1 / .LJ$m_air + 1 / .LJ$m_h2o) * 1013.25 * 1e-4

.lj_frac <- function(x) x - trunc(x)

# Saturation vapour pressure over water (hPa), Buck (1981).
.lj_esat <- function(tk) 1.004 * 6.1121 * exp(17.502 * (tk - 273.15) / (tk - 32.18))

.lj_dew_point <- function(e) {
  z <- log(e / (6.1121 * 1.004))
  273.15 + 240.97 * z / (17.502 - z)
}

.lj_viscosity <- function(tk) {
  omega <- (tk / 97 - 2.9) / 0.4 * (-0.034) + 1.048
  2.6693e-6 * sqrt(.LJ$m_air * tk) / (3.617^2 * omega)
}

.lj_diffusivity <- function(tk, pres) .LJ$diff_coef * (tk / .LJ$tcrit12)^2.334 / pres

.lj_density <- function(tk, pres) pres * 100 / (.LJ$r_air * tk)

.lj_evap <- function(tk) (313.15 - tk) / 30 * (-71100) + 2.4073e6

.lj_emis_atm <- function(tk, rh) 0.575 * (rh * .lj_esat(tk))^0.143

# Convective heat transfer coefficients; air properties evaluated once by the caller.
.lj_h_sphere <- function(density, visc, speed) {
  re <- pmax(speed, .LJ$min_speed) * density * .LJ$d_globe / visc
  nu <- 2 + 0.6 * sqrt(re) * .LJ$pr^0.3333
  nu * .LJ$k_visc * visc / .LJ$d_globe
}

.lj_h_cylinder <- function(density, visc, speed) {
  re <- pmax(speed, .LJ$min_speed) * density * .LJ$d_wick / visc
  nu <- 0.281 * re^0.6 * .LJ$pr^0.44
  nu * .LJ$k_visc * visc / .LJ$d_wick
}

# Damped fixed-point iteration run over all rows at once; NA where it fails.
.lj_iterate <- function(init, step) {
  prev <- init
  out <- rep(NA_real_, length(init))
  active <- which(!is.na(init))
  for (iter in seq_len(.LJ$max_iter)) {
    if (!length(active)) break
    new <- step(prev[active], active)
    done <- is.na(new) | abs(new - prev[active]) < .LJ$convergence
    ok <- done & !is.na(new)
    out[active[ok]] <- new[ok]
    prev[active] <- 0.9 * prev[active] + 0.1 * new
    active <- active[!done]
  }
  out
}

# Sun position from the low-precision Astronomical Almanac formulae
# (solarposition() by Nels Larson, PNNL), refraction included.
.lj_solar_position <- function(datetime, lat, lon) {
  secs <- as.numeric(datetime)
  ut <- (secs %% 86400) / 3600
  d <- (secs - 946728000) / 86400
  cent <- (d - ut / 24) / 36525

  ma <- .lj_frac((357.528 + 0.9856003 * d) / 360) * 2 * pi
  ml <- .lj_frac((280.460 + 0.9856474 * d) / 360) * 2 * pi
  obl <- (23.439 - 4e-7 * d) * pi / 180
  el <- (1.915 * sin(ma) + 0.020 * sin(2 * ma)) * pi / 180 + ml
  dist <- 1.00014 - 0.01671 * cos(ma) - 0.00014 * cos(2 * ma)

  ra <- atan2(cos(obl) * sin(el), cos(el))
  ra <- ifelse(ra < 0, ra + 2 * pi, ra)
  ra <- .lj_frac(ra / (2 * pi)) * 24
  dec <- asin(sin(obl) * sin(el))

  gmst <- 24110.54841 + cent * (8640184.812866 + cent * (0.093104 - cent * 6.2e-6))
  gmst <- .lj_frac(gmst / 3600 / 24) * 24
  gmst <- ifelse(gmst < 0, gmst + 24, gmst)
  lmst <- .lj_frac((gmst + ut * 1.00273790934 + lon / 15) / 24) * 24
  lmst <- ifelse(lmst < 0, lmst + 24, lmst)

  ha <- lmst - ra
  ha <- ifelse(ha < -12, ha + 24, ifelse(ha > 12, ha - 24, ha)) / 24 * 2 * pi
  latr <- lat * pi / 180
  alt <- asin(sin(dec) * sin(latr) + cos(dec) * cos(ha) * cos(latr))
  tan_alt <- ifelse(abs(alt) < 1.57079615, tan(alt), 6e6)
  alt <- alt * 180 / pi

  refr <- ifelse(
    alt < 19.225,
    (0.1594 + alt * (0.0196 + 0.00002 * alt)) * 1013.25 /
      ((1 + alt * (0.505 + 0.0845 * alt)) * 288),
    0.00452 * (1013.25 / 288) / tan_alt
  )
  refr[alt < -1 | tan_alt == 6e6] <- 0
  list(cza = cos((90 - (alt + refr)) * pi / 180), dist = dist)
}

# Caps solar at 85% of top-of-atmosphere and splits off the direct beam.
.lj_solar_parameters <- function(solar, cza, dist) {
  toa <- .LJ$solar_const * pmax(0, cza) / dist^2
  toa[cza < .LJ$cza_min] <- 0
  day <- toa > 0
  norm <- ifelse(day, pmin(solar / toa, .LJ$normsolar_max), 0)
  solar <- ifelse(day, norm * toa, solar)
  fdir <- ifelse(day & norm > 0, pmax(pmin(exp(3 - 1.34 * norm - 1.65 / norm), 0.9), 0), 0)
  list(solar = solar, fdir = fdir)
}

# EPA solar-radiation/delta-T stability class (EPA-454/5-99-005, 6.2.5).
.lj_stability <- function(daytime, speed, solar, delta_t) {
  lsrdt <- rbind(
    c(1, 1, 2, 4, 0, 5, 6, 0), c(1, 2, 3, 4, 0, 5, 6, 0),
    c(2, 2, 3, 4, 0, 4, 4, 0), c(3, 3, 4, 4, 0, 0, 0, 0),
    c(3, 4, 4, 4, 0, 0, 0, 0), c(0, 0, 0, 0, 0, 0, 0, 0)
  )
  j <- ifelse(daytime,
    findInterval(-solar, -c(Inf, 925, 675, 175), left.open = TRUE) - 1L,
    ifelse(delta_t >= 0, 6L, 5L)
  )
  i <- ifelse(daytime,
    findInterval(speed, c(2, 3, 5, 6)),
    findInterval(speed, c(2, 2.5))
  )
  lsrdt[cbind(i + 1L, j + 1L)]
}

.lj_wind_at_2m <- function(speed, height, stability, urban) {
  exps <- if (urban) c(0.15, 0.15, 0.20, 0.25, 0.30, 0.30) else c(0.07, 0.07, 0.10, 0.15, 0.35, 0.55)
  pmax(speed * (.LJ$ref_height / height)^exps[stability], .LJ$min_speed)
}

.lj_sky <- function(tk, rh) 0.5 * (.lj_emis_atm(tk, rh) * tk^4 + .LJ$emis_sfc * tk^4)

.lj_globe <- function(tk, sky, pres, speed, solar, fdir, cza) {
  beam <- ifelse(fdir > 0, fdir * (1 / (2 * cza) - 1), 0)
  sun <- solar / (2 * .LJ$stefanb * .LJ$emis_globe) * (1 - .LJ$alb_globe) * (beam + 1 + .LJ$alb_sfc)
  out <- .lj_iterate(tk, function(prev, i) {
    tref <- 0.5 * (prev + tk[i])
    h <- .lj_h_sphere(.lj_density(tref, pres[i]), .lj_viscosity(tref), speed[i])
    (sky[i] - h / (.LJ$stefanb * .LJ$emis_globe) * (prev - tk[i]) + sun[i])^0.25
  })
  out - 273.15
}

.lj_wet_bulb <- function(tk, rh, sky, pres, speed, solar, fdir, cza, natural) {
  eair <- rh * .lj_esat(tk)
  edge <- 0.25 * .LJ$d_wick / .LJ$l_wick
  beam <- ifelse(fdir > 0, fdir * (tan(acos(cza)) / pi + edge), 0)
  sun <- (1 - .LJ$alb_wick) * solar * ((1 - fdir) * (1 + edge) + beam + .LJ$alb_sfc)
  out <- .lj_iterate(.lj_dew_point(eair), function(prev, i) {
    tref <- 0.5 * (prev + tk[i])
    visc <- .lj_viscosity(tref)
    density <- .lj_density(tref, pres[i])
    h <- .lj_h_cylinder(density, visc, speed[i])
    fatm <- .LJ$stefanb * .LJ$emis_wick * (sky[i] - prev^4) + sun[i]
    ewick <- .lj_esat(prev)
    sc <- visc / (density * .lj_diffusivity(tref, pres[i]))
    tk[i] - .lj_evap(tref) / .LJ$ratio * (ewick - eair[i]) / (pres[i] - ewick) *
      (.LJ$pr / sc)^0.56 + fatm / h * natural
  })
  out - 273.15
}

#' Outdoor Wet Bulb Globe Temperature (Liljegren method)
#'
#' Physically based outdoor WBGT from standard meteorological variables,
#' following Liljegren et al. (2008). Globe and natural wet bulb temperatures
#' are solved iteratively from energy balances that include direct and diffuse
#' solar radiation, so this is the sun-exposed WBGT of ISO 7243. Inputs should
#' be instantaneous or hourly values; for ERA5, `solar` is the hourly
#' accumulated surface solar radiation downwards divided by 3600 and
#' `datetime` the middle of the accumulation hour.
#'
#' This product includes software produced by UChicago Argonne, LLC under
#' Contract No. DE-AC02-06CH11357 with the Department of Energy.
#'
#' @param temp_c Air temperature (degrees Celsius).
#' @param rh Relative humidity (percent).
#' @param wind_speed Wind speed (m/s) measured at `wind_height`.
#' @param solar Global horizontal solar irradiance (W/m2).
#' @param datetime `POSIXct` time of each observation; converted to UTC.
#' @param lat,lon Latitude and longitude (decimal degrees).
#' @param pressure Surface pressure (hPa).
#' @param wind_height Height of the wind measurement (m). Values other than 2
#'   are scaled to 2 m with a stability-dependent power law.
#' @param urban Use the urban (`TRUE`) or rural (`FALSE`) power-law exponents.
#' @param delta_t Vertical temperature difference, upper minus lower level
#'   (degrees Celsius); sets the night-time stability class only.
#' @param components If `TRUE`, return globe, natural wet bulb and psychrometric
#'   wet bulb temperatures as well.
#' @return A numeric vector of WBGT (degrees Celsius), or with
#'   `components = TRUE` a data.frame with columns `wbgt`, `globe`,
#'   `natural_wet_bulb`, `wet_bulb` and `wind_2m`. `NA` where the iteration
#'   does not converge.
#' @references Liljegren, J.C., Carhart, R.A., Lawday, P., Tschopp, S. & Sharp,
#'   R. (2008). Modeling the Wet Bulb Globe Temperature Using Standard
#'   Meteorological Measurements. Journal of Occupational and Environmental
#'   Hygiene, 5(10), 645-655. \doi{10.1080/15459620802310770}
#' @seealso [wbgt()] to choose between this and the closed-form estimate.
#' @export
#' @examples
#' t <- as.POSIXct("2024-05-20 08:30:00", tz = "UTC") # 14:00 IST
#' wbgt_liljegren(42,
#'   rh = 25, wind_speed = 3, solar = 850,
#'   datetime = t, lat = 26.9, lon = 75.8
#' )
#' wbgt_liljegren(42, 25, 3, 850, t, 26.9, 75.8, components = TRUE)
wbgt_liljegren <- function(temp_c, rh, wind_speed, solar, datetime, lat, lon,
                           pressure = 1013.25, wind_height = 10, urban = FALSE,
                           delta_t = 0, components = FALSE) {
  if (!inherits(datetime, "POSIXct")) stop("datetime must be POSIXct")
  v <- list(ta = temp_c, rh = rh, speed = wind_speed, solar = solar, lat = lat, lon = lon, pres = pressure, delta_t = delta_t)
  n <- max(lengths(v), length(datetime))
  v <- lapply(v, function(x) rep_len(as.numeric(x), n))
  ta <- v$ta
  tk <- ta + 273.15
  rhf <- v$rh / 100
  speed <- v$speed
  pres <- v$pres
  pos <- .lj_solar_position(rep_len(datetime, n), v$lat, v$lon)
  sp <- .lj_solar_parameters(v$solar, pos$cza, pos$dist)

  if (wind_height != .LJ$ref_height) {
    stab <- .lj_stability(pos$cza > 0, speed, sp$solar, v$delta_t)
    speed <- .lj_wind_at_2m(speed, wind_height, stab, urban)
  }

  sky <- .lj_sky(tk, rhf)
  globe <- .lj_globe(tk, sky, pres, speed, sp$solar, sp$fdir, pos$cza)
  nwb <- .lj_wet_bulb(tk, rhf, sky, pres, speed, sp$solar, sp$fdir, pos$cza, 1)
  out <- 0.1 * ta + 0.2 * globe + 0.7 * nwb
  if (!components) {
    return(out)
  }
  data.frame(
    wbgt = out, globe = globe, natural_wet_bulb = nwb,
    wet_bulb = .lj_wet_bulb(tk, rhf, sky, pres, speed, sp$solar, sp$fdir, pos$cza, 0),
    wind_2m = speed
  )
}

#' Wet Bulb Globe Temperature
#'
#' Computes WBGT by one of two methods:
#' * `"simple"`: the Australian Bureau of Meteorology closed form
#'   `0.567 * T + 0.393 * e + 3.94` from temperature and dewpoint only
#'   ([wbgt_simple()]). Assumes moderate sun and light wind; suited to daily
#'   data.
#' * `"liljegren"`: the physical outdoor model of [wbgt_liljegren()], which
#'   needs wind, solar radiation, time and location; suited to hourly data.
#'
#' @param temp_c Air temperature (degrees Celsius).
#' @param dewpoint_c Dewpoint temperature (degrees Celsius).
#' @param method `"simple"` or `"liljegren"`.
#' @param ... For `method = "liljegren"`, arguments passed to
#'   [wbgt_liljegren()]: `wind_speed`, `solar`, `datetime`, `lat`, `lon` and
#'   optionally `pressure`, `wind_height`, `urban`, `delta_t`.
#' @return A numeric vector of WBGT (degrees Celsius).
#' @export
#' @examples
#' wbgt(38, 24)
#' wbgt(38, 24,
#'   method = "liljegren", wind_speed = 3, solar = 800,
#'   datetime = as.POSIXct("2024-05-20 08:30:00", tz = "UTC"),
#'   lat = 26.9, lon = 75.8
#' )
wbgt <- function(temp_c, dewpoint_c, method = c("simple", "liljegren"), ...) {
  method <- match.arg(method)
  if (method == "simple") {
    return(wbgt_simple(temp_c, dewpoint_c))
  }
  rh <- 100 * .lj_esat(dewpoint_c + 273.15) / .lj_esat(temp_c + 273.15)
  wbgt_liljegren(temp_c, rh = pmin(rh, 100), ...)
}
