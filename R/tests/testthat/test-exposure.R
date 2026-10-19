# Constant-baseline series make normals and percentiles known exactly.

base_dates <- seq(as.Date("2001-01-01"), as.Date("2003-12-31"), by = "day")

series <- function(tmax_base, tmin_base = tmax_base - 14) {
  data.frame(date = base_dates, tmax = tmax_base, tmin = tmin_base)
}

set_days <- function(x, from, n, value) {
  i <- which(base_dates == as.Date(from)) + seq_len(n) - 1L
  x[i] <- value
  x
}

hw <- function(s, ...) heatwave_days(s$date, s$tmax, s$tmin, baseline = c(2001, 2002), ...)

test_that("IMD plains heatwave: Tmax >= 40 C with departure >= 4.5 C on 2+ days", {
  s <- series(38) # normal 38 C
  s$tmax <- set_days(s$tmax, "2003-05-01", 2, 42.5) # departure exactly 4.5
  s$tmax <- set_days(s$tmax, "2003-05-10", 2, 42.4) # departure 4.4
  s$tmax <- set_days(s$tmax, "2003-05-20", 1, 46) # one day only
  s$tmax <- set_days(s$tmax, "2003-06-01", 3, 44.5) # departure 6.5: severe
  r <- hw(s)
  expect_equal(as.character(r$date[r$day]), c("2003-05-01", "2003-05-02", "2003-06-01", "2003-06-02", "2003-06-03"))
  expect_equal(r$spell_length[r$spell_start], c(2L, 3L))
  expect_equal(as.character(r$date[r$severe]), c("2003-06-01", "2003-06-02", "2003-06-03"))
})

test_that("IMD plains heatwave: Tmax >= 45 C regardless of departure; severe at 47 C", {
  s <- series(42) # normal above 40 C
  s$tmax <- set_days(s$tmax, "2003-05-01", 2, 45) # departure 3
  s$tmax <- set_days(s$tmax, "2003-05-10", 2, 44.9)
  s$tmax <- set_days(s$tmax, "2003-05-20", 2, 47)
  r <- hw(s)
  expect_equal(sum(r$spell_start), 2)
  expect_equal(as.character(r$date[r$severe]), c("2003-05-20", "2003-05-21"))
})

test_that("IMD coastal (37 C) and hilly (30 C) floors apply", {
  s <- series(33)
  s$tmax <- set_days(s$tmax, "2003-05-01", 2, 37.5) # >= 37, departure 4.5
  expect_equal(sum(hw(s, terrain = "coastal")$day), 2)
  expect_equal(sum(hw(s, terrain = "plains")$day), 0) # below 40 C
  s <- series(24)
  s$tmax <- set_days(s$tmax, "2003-05-01", 2, 28.5) # departure 4.5 but below 30 C
  s$tmax <- set_days(s$tmax, "2003-06-01", 2, 30) # departure 6
  r <- hw(s, terrain = "hilly")
  expect_equal(as.character(r$date[r$day]), c("2003-06-01", "2003-06-02"))
  # the 45 C and 47 C absolute criteria apply in every terrain
  s <- series(42)
  s$tmax <- set_days(s$tmax, "2003-05-01", 2, 45)
  s$tmax <- set_days(s$tmax, "2003-05-10", 2, 47)
  for (t in c("hilly", "coastal")) {
    r <- hw(s, terrain = t)
    expect_equal(sum(r$day), 4, info = t)
    expect_equal(as.character(r$date[r$severe]), c("2003-05-10", "2003-05-11"), info = t)
  }
})

test_that("IMD coastal severe needs the 40 C floor", {
  s <- series(31)
  s$tmax <- set_days(s$tmax, "2003-05-01", 2, 38) # departure 7, Tmax below 40
  s$tmax <- set_days(s$tmax, "2003-05-10", 2, 40) # departure 9
  r <- hw(s, terrain = "coastal")
  expect_equal(sum(r$day), 4)
  expect_equal(as.character(r$date[r$severe]), c("2003-05-10", "2003-05-11"))
  expect_equal(sum(hw(s, terrain = "hilly")$severe), 4)
})

test_that("percentile heatwave needs 3+ days above the calendar-day 90th percentile", {
  s <- series(35)
  s$tmax <- set_days(s$tmax, "2003-05-01", 3, 35.1)
  s$tmax <- set_days(s$tmax, "2003-06-01", 2, 39)
  r <- hw(s, method = "percentile")
  expect_equal(as.character(r$date[r$day]), c("2003-05-01", "2003-05-02", "2003-05-03"))
  expect_equal(sum(hw(s, method = "percentile", min_duration = 2)$spell_start), 2)
})

test_that("excess_heat_factor follows Nairn & Fawcett (2015)", {
  s <- series(40, 26) # DMT = 33 everywhere in the baseline
  k <- which(base_dates == as.Date("2003-06-10"))
  s$tmax[k + 0:2] <- 44
  s$tmin[k + 1:3] <- 30 # the nights following the hot days
  e <- excess_heat_factor(s$date, s$tmax, s$tmin, baseline = c(2001, 2002))
  expect_equal(attr(e, "t95"), 33)
  expect_equal(e$dmt[k + 0:2], c(37, 37, 37)) # (Tmax_i + Tmin_i+1) / 2
  # EHI_sig = EHI_accl = 37 - 33 = 4, EHF = 4 * max(1, 4)
  expect_equal(e$ehi_sig[k], 4)
  expect_equal(e$ehi_accl[k], 4)
  expect_equal(e$ehf[k], 16)
  # period starting the day before: three-day mean (33 + 37 + 37) / 3
  expect_equal(e$ehf[k - 1], (107 / 3 - 33)^2)
  expect_true(is.na(e$ehf[1])) # no 30-day history yet
  expect_true(all(abs(e$ehf[!is.na(e$ehf) & s$date < as.Date("2003-01-01")]) < 1e-12))

  r <- hw(s, method = "ehf")
  first <- which(e$ehf > 0)[1]
  expect_equal(r$date[which(r$day)[1]], s$date[first])
  s0 <- series(40)
  expect_error(heatwave_days(s0$date, s0$tmax, method = "ehf", baseline = c(2001, 2002)), "tmin")
})

test_that("IMD warm nights need Tmax >= 40 C and Tmin departure >= 4.5 C", {
  s <- series(41, 27) # Tmin normal 27
  s$tmin <- set_days(s$tmin, "2003-05-01", 2, 31.5) # departure 4.5
  s$tmin <- set_days(s$tmin, "2003-05-10", 1, 34) # departure 7: very warm
  s$tmax <- set_days(s$tmax, "2003-05-10", 1, 41)
  s$tmin <- set_days(s$tmin, "2003-06-01", 1, 33)
  s$tmax <- set_days(s$tmax, "2003-06-01", 1, 39.9) # Tmax below 40
  r <- warm_nights(s$date, s$tmin, s$tmax, baseline = c(2001, 2002))
  expect_equal(as.character(r$date[r$day]), c("2003-05-01", "2003-05-02", "2003-05-10"))
  expect_equal(as.character(r$date[r$severe]), "2003-05-10")
  expect_equal(r$spell_length[r$spell_start], c(2L, 1L))
  expect_error(warm_nights(s$date, s$tmin, baseline = c(2001, 2002)), "tmax")
})

test_that("absolute and percentile warm nights", {
  s <- series(40, 24)
  s$tmin <- set_days(s$tmin, "2003-05-01", 3, 26)
  expect_equal(sum(warm_nights(s$date, s$tmin, method = "absolute", threshold = 25)$day), 3)
  expect_equal(sum(warm_nights(s$date, s$tmin, method = "absolute")$day), nrow(s)) # TR: > 20 C
  expect_equal(sum(warm_nights(s$date, s$tmin, method = "percentile", baseline = c(2001, 2002))$day), 3)
})

test_that("spells break at gaps in the dates", {
  d <- as.Date(c("2003-05-01", "2003-05-02", "2003-05-04", "2003-05-05", "2003-05-06"))
  s <- varunayan:::.spells(rep(TRUE, 5), d, 3)
  expect_equal(s$in_spell, c(FALSE, FALSE, TRUE, TRUE, TRUE))
  expect_equal(s$length, c(0L, 0L, 3L, 0L, 0L))
})

test_that("calendar days pool 29 February with 28 February", {
  d <- as.Date(c("2004-02-28", "2004-02-29", "2004-03-01", "2003-03-01"))
  expect_equal(varunayan:::.doy365(d), c(59L, 59L, 60L, 60L))
})

test_that("input checks", {
  s <- series(38)
  expect_error(hw(s[c(2, 1, 3:10), ]), "increasing")
  expect_error(heatwave_days(s$date, s$tmax[-1], baseline = c(2001, 2002)), "same length")
  expect_error(heatwave_days(s$date, s$tmax, baseline = c(1980, 1990)), "no days in the baseline")
  expect_error(heatwave_days(s$date, s$tmax, baseline = 2001), "c\\(first_year")
  gap <- s[-100, ]
  e <- excess_heat_factor(gap$date, gap$tmax, gap$tmin, c(2001, 2002))
  expect_equal(e$date, gap$date)
  expect_true(is.na(e$dmt[99])) # the day before the gap has no following night
})

test_that("exposure_indicators summarises per location and period", {
  a <- series(38)
  a$tmax <- set_days(a$tmax, "2003-05-01", 3, 43)
  a$latitude <- 26.5
  a$longitude <- 75.5
  b <- series(30)
  b$latitude <- 26.5
  b$longitude <- 76.5
  daily <- rbind(a, b)
  daily$dewpoint <- 20
  out <- exposure_indicators(daily, baseline = c(2001, 2002))
  expect_equal(nrow(out), 6)
  r <- out[out$longitude == 75.5 & out$year == 2003, ]
  expect_equal(r$heatwave_days, 3)
  expect_equal(r$heatwave_events, 1)
  expect_equal(r$heatwave_longest, 3)
  expect_equal(r$hot_days, 3)
  expect_equal(r$dtr_mean, 14 + 3 * 5 / 365)
  expect_equal(r$tx90p, 100 * 3 / 365)
  expect_equal(r$tropical_nights, 365) # Tmin 24 C
  expect_equal(r$wbgt_max, wbgt_simple(43, 20))
  expect_equal(r$heat_index_max, heat_index(43, relative_humidity_from_dewpoint(43, 20)))
  expect_equal(out$heatwave_days[out$longitude == 76.5], c(0, 0, 0))

  m <- exposure_indicators(daily[daily$longitude == 75.5, ], baseline = c(2001, 2002), period = "month", months = 5)
  expect_equal(nrow(m), 3)
  expect_equal(m$month, c(5L, 5L, 5L))
  expect_equal(m$heatwave_days, c(0, 0, 3))

  expect_error(exposure_indicators(daily[, c("date", "tmax")], by = NULL), "tmin")
  expect_error(exposure_indicators(daily, by = NULL, baseline = c(2001, 2002)), "duplicate dates")
})

test_that("exposure_indicators fills missing days so spells do not bridge gaps", {
  s <- series(38)
  s$tmax <- set_days(s$tmax, "2003-05-01", 5, 43)
  s <- s[s$date != as.Date("2003-05-03"), ]
  out <- exposure_indicators(s, by = NULL, baseline = c(2001, 2002), terrain = "plains")
  expect_equal(out$heatwave_events[out$year == 2003], 2)
  expect_equal(out$n_days[out$year == 2003], 364)
  ehf <- exposure_indicators(s, by = NULL, baseline = c(2001, 2002), heatwave_method = "ehf")
  expect_equal(nrow(ehf), 3)
})

test_that("imd_terrain classifies hill, coastal and plains cells", {
  expect_equal(
    imd_terrain(c(31.1, 27.3, 28.6, 26.9, 13.1, 19.1), c(77.2, 88.6, 77.2, 75.8, 80.3, 72.9)),
    c("hilly", "hilly", "plains", "plains", "coastal", "coastal")
  )
  expect_equal(imd_terrain(31.1, 77.2, hill_elevation = 3000), "hilly") # Himachal Pradesh
  expect_equal(imd_terrain(27.3, 88.6, hill_elevation = 3000), "plains")
  expect_equal(imd_terrain(c(32.73, 32.27), c(74.86, 75.65)), c("hilly", "plains")) # Jammu, Pathankot
  expect_true(is.na(imd_terrain(13.5, 80.5))) # offshore IMD cell centre
  expect_equal(imd_terrain(13.5, 80.5, cell_size = 1), "coastal")
  expect_true(all(is.na(imd_terrain(c(0, 15), c(0, 65)))))
})

test_that("india_elevation reads local elevation", {
  e <- india_elevation(c(31.10, 34.16, 28.61, 13.08), c(77.17, 77.58, 77.21, 80.27)) # Shimla, Leh, Delhi, Chennai
  expect_true(e[1] > 1800 && e[1] < 2400)
  expect_true(e[2] > 3000 && e[2] < 3800)
  expect_true(e[3] > 150 && e[3] < 300)
  expect_true(e[4] < 30)
  expect_true(all(is.na(india_elevation(c(0, 15), c(0, 65)))))
})

test_that("terrain = 'auto' applies the hilly floor per location", {
  s <- series(25) # normal 25 C
  s$tmax <- set_days(s$tmax, "2003-05-01", 2, 31) # departure 6: hilly heatwave only
  s$tmin <- 15
  hill <- cbind(s, latitude = 31.5, longitude = 77.5)
  plain <- cbind(s, latitude = 28.5, longitude = 77.5)
  out <- exposure_indicators(rbind(hill, plain), baseline = c(2001, 2002))
  y <- out[out$year == 2003, ]
  expect_equal(y$terrain[y$latitude == 31.5], "hilly")
  expect_equal(y$heatwave_days[y$latitude == 31.5], 2)
  expect_equal(y$terrain[y$latitude == 28.5], "plains")
  expect_equal(y$heatwave_days[y$latitude == 28.5], 0)

  expect_error(exposure_indicators(s, by = NULL, baseline = c(2001, 2002)), "latitude and longitude")
  expect_error(exposure_indicators(cbind(s, latitude = 0.5, longitude = 0.5), baseline = c(2001, 2002)), "outside the IMD")
  expect_false("terrain" %in% names(exposure_indicators(hill, baseline = c(2001, 2002), terrain = "hilly")))
})

test_that("a precomputed wbgt column replaces the BoM estimate", {
  s <- series(38)
  s$wbgt <- 25
  out <- exposure_indicators(s, by = NULL, baseline = c(2001, 2002), terrain = "plains")
  expect_equal(out$wbgt_max, c(25, 25, 25))
  expect_false("heat_index_max" %in% names(out))
})

test_that("imd_exposure_bbox downloads tmax and tmin over the baseline and reports the requested years", {
  calls <- list()
  local_mocked_bindings(imd_temperature_bbox = function(request_id, start_year, end_year, north, south,
                                                        east, west, var_type, ...) {
    calls[[var_type]] <<- c(start_year, end_year)
    s <- series(if (var_type == "tmax") 38 else 24)
    data.frame(date = s$date, latitude = 26.5, longitude = 75.5, temperature = s$tmax)
  })
  out <- imd_exposure_bbox(2003, 2003, 27, 26, 76, 75, baseline = c(2001, 2002))
  expect_equal(calls$tmax, c(2001, 2003))
  expect_equal(calls$tmin, c(2001, 2003))
  expect_equal(out$year, 2003L)
  expect_equal(out$tmin_mean, 24)
  expect_equal(IMDExposureBbox(2003, 2003, 27, 26, 76, 75, baseline = c(2001, 2002)), out)
})
