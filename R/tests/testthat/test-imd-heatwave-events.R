# IMD bulletin heatwaves (24 h before issue) vs the 1 degree grid.

fixture <- function(name) {
  d <- utils::read.delim(test_path("fixtures", name), encoding = "UTF-8")
  d$date <- as.Date(d$date)
  d
}

# 1 degree cell centres covering each meteorological sub-division
subdivisions <- utils::read.csv(text = "
subdivision,south,north,west,east
west_rajasthan,24.5,29.5,69.5,73.5
east_rajasthan,23.5,27.5,74.5,77.5
jammu_division,32.5,33.5,73.5,75.5
himachal_pradesh,31.5,32.5,75.5,78.5
punjab,29.5,31.5,73.5,76.5
haryana_delhi,28.5,30.5,74.5,77.5
west_uttar_pradesh,26.5,29.5,77.5,79.5
uttar_pradesh,24.5,29.5,77.5,83.5
west_bengal,21.5,26.5,86.5,89.5
gangetic_west_bengal,21.5,24.5,86.5,88.5
bihar,24.5,26.5,83.5,87.5
odisha,18.5,22.5,82.5,86.5
coastal_andhra,15.5,18.5,79.5,83.5
chhattisgarh,18.5,23.5,80.5,83.5
vidarbha,19.5,21.5,76.5,79.5
saurashtra_kutch,21.5,23.5,68.5,71.5
")

# all-India daily flags, built once per run
imd_flags <- local({
  flags <- NULL
  function() {
    if (!is.null(flags)) {
      return(flags)
    }
    cache <- Sys.getenv("VARUNAYAN_LIVE_CACHE")
    if (nzchar(cache)) withr::local_options(varunayan.cache_dir = cache)
    d <- suppressMessages(.imd_daily_tmax_tmin(c(1991, 2025), 37.5, 6.5, 97.5, 67.5, withr::local_tempdir()))
    loc <- unique(d[, c("latitude", "longitude")])
    loc[, terrain := imd_terrain(latitude, longitude, cell_size = 1)]
    d <- d[loc[!is.na(terrain)], on = c("latitude", "longitude")]
    f <- d[, .exposure_daily(.SD, c(1991, 2020), "imd", "imd", .BY$terrain), by = .(latitude, longitude, terrain)]
    flags <<- data.table::setkey(f[, .(latitude, longitude, terrain, date, tmax, tmin, hw = hw_day, severe = hw_severe, wn = wn_day)], date)
    flags
  }
})

region_on <- function(subdivision, day) {
  b <- subdivisions[subdivisions$subdivision == subdivision, ]
  f <- imd_flags()[.(day)]
  f[f$latitude >= b$south & f$latitude <= b$north & f$longitude >= b$west & f$longitude <= b$east, ]
}

events <- fixture("imd_heatwave_events.tsv")

test_that("each fixture row quotes a heat bulletin issued the day after the event", {
  expect_true(all(events$subdivision %in% subdivisions$subdivision))
  expect_true(all(events$indicator %in% c("heatwave", "warm_night")))
  expect_true(all(grepl("heat ?wave|warm night", events$quote, ignore.case = TRUE)))
  expect_true(all(format(events$date + 1, "%Y%m%d") == substr(basename(events$bulletin), 1, 8)))
})

test_that("each heat wave IMD reported is a heatwave day in the grid", {
  skip_live_imd()
  # few_cells: 1 degree Tmax reaches the floor in fewer cells than the bulletin's extent
  hw <- events[events$indicator == "heatwave" & events$grid %in% c("detected", "few_cells"), ]
  expect_gt(nrow(hw), 30)
  for (i in seq_len(nrow(hw))) {
    r <- region_on(hw$subdivision[i], hw$date[i])
    expect_gt(sum(r$hw), 0, label = sprintf("%s %s: %s", hw$date[i], hw$subdivision[i], hw$quote[i]))
  }
})

test_that("heat waves over 'most parts' cover more than isolated pockets of the grid", {
  skip_live_imd()
  most <- events[events$indicator == "heatwave" & events$extent == "most parts" & events$grid == "detected", ]
  for (i in seq_len(nrow(most))) {
    r <- region_on(most$subdivision[i], most$date[i])
    # IMD calls 25% of stations or fewer "isolated"
    expect_gt(mean(r$hw), 0.25, label = sprintf("%s %s", most$date[i], most$subdivision[i]))
  }
})

test_that("severe heat wave at most parts of West Rajasthan, 16 and 17 March 2022, is severe in the grid", {
  skip_live_imd()
  for (d in c("2022-03-16", "2022-03-17")) {
    r <- region_on("west_rajasthan", as.Date(d))
    expect_gt(mean(r$severe), 0.25, label = d)
  }
})

test_that("the May 2024 West Rajasthan heatwave is one unbroken spell at Phalodi", {
  skip_live_imd()
  days <- seq(as.Date("2024-05-22"), as.Date("2024-05-29"), by = "day")
  for (d in as.list(days)) {
    expect_gt(sum(region_on("west_rajasthan", d)$hw), 0, label = format(d))
  }
  pk <- imd_flags()[.(days)][latitude == 27.5 & longitude == 72.5] # Phalodi
  expect_true(all(pk$hw))
})

test_that("each warm night IMD reported is a warm night in the grid", {
  skip_live_imd()
  wn <- events[events$indicator == "warm_night" & events$grid == "detected", ]
  for (i in seq_len(nrow(wn))) {
    r <- region_on(wn$subdivision[i], wn$date[i])
    expect_gt(sum(r$wn), 0, label = sprintf("%s %s: %s", wn$date[i], wn$subdivision[i], wn$quote[i]))
  }
})

test_that("no grid cell has a heat wave on days IMD bulletins report NIL", {
  skip_live_imd()
  nil <- fixture("imd_nil_days.tsv")
  f <- imd_flags()
  for (i in seq_len(nrow(nil))) {
    day <- f[.(nil$date[i])]
    expect_gt(nrow(day), 300)
    expect_equal(sum(day$hw), 0, label = sprintf("%s: %s", nil$date[i], nil$quote[i]))
  }
})

test_that("the cell of the country's hottest station is among India's hottest cells that day", {
  skip_live_imd()
  st <- fixture("imd_station_maxima.tsv")
  f <- imd_flags()
  for (i in seq_len(nrow(st))) {
    day <- f[.(st$date[i])]
    cell <- day[day$latitude == floor(st$latitude[i]) + 0.5 & day$longitude == floor(st$longitude[i]) + 0.5, ]
    lab <- sprintf("%s %s", st$station[i], st$date[i])
    expect_equal(nrow(cell), 1, label = lab)
    # a 1 degree average sits below the hottest station but above the plains floor
    expect_lte(cell$tmax, st$tmax_c[i] + 0.5, label = lab)
    expect_gte(cell$tmax, 40, label = lab)
    expect_gte(mean(day$tmax < cell$tmax), 0.75, label = lab)
  }
})

test_that("events the 1 degree grid under-resolves still fall short", {
  skip_live_imd()
  few <- events[events$grid == "few_cells", ]
  for (i in seq_len(nrow(few))) {
    hw <- region_on(few$subdivision[i], few$date[i])$hw
    expect_true(any(hw) && mean(hw) <= 0.25, label = few$subdivision[i])
  }
  small <- events[events$grid == "below_grid_scale", ]
  for (i in seq_len(nrow(small))) {
    expect_false(any(region_on(small$subdivision[i], small$date[i])$wn), label = small$subdivision[i])
  }
})
