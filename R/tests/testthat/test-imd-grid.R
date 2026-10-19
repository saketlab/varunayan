# IMD readers on synthetic grids where each value encodes its lon, lat and day.

# Value for a temperature cell: integer part from longitude, fraction from
# latitude and day. All terms are exact in float32 and stay below 99.
imd_temp_code <- function(lon, lat, day) {
  (lon - 66.5) + (lat - 6.5) / 64 + (day %% 8) / 1024
}

# Sea cells, masked with 99.9, are about a fifth of the grid; one land cell is NaN.
imd_is_sea <- function(ilon, ilat) (ilon + 2 * ilat) %% 5 == 0
imd_nan_cell <- c(10, 11)
cell_index <- function(df) list(ilon = df$longitude - 66.5, ilat = df$latitude - 6.5)

write_full_temperature <- function(path, year) {
  lons <- imd_fx_temp_lons()
  lats <- imd_fx_temp_lats()
  g <- expand.grid(ilon = seq_along(lons), ilat = seq_along(lats), day = seq_len(days_in_year(year)))
  v <- imd_temp_code(lons[g$ilon], lats[g$ilat], g$day)
  v[imd_is_sea(g$ilon, g$ilat)] <- 99.9
  v[g$ilon == imd_nan_cell[1] & g$ilat == imd_nan_cell[2]] <- NaN
  con <- file(path, "wb")
  on.exit(close(con))
  writeBin(v, con, size = 4, endian = "little")
  invisible(path)
}

n_temp_land <- function() {
  g <- expand.grid(ilon = 1:31, ilat = 1:31)
  sum(!imd_is_sea(g$ilon, g$ilat)) - 1L # minus the NaN cell, which is land
}

# written once and shared by the read-only tests below
temp_2023 <- write_full_temperature(tempfile(fileext = ".grd"), 2023)

# ---- temperature reader ---------------------------------------------------

test_that("read_imd_temperature places every cell of the 31 x 31 grid correctly", {
  df <- suppressMessages(read_imd_temperature(temp_2023, "tmax", 2023))
  expect_equal(nrow(df), n_temp_land() * 365L)
  day <- as.integer(df$date - as.Date("2023-01-01")) + 1L
  expect_identical(
    as.numeric(df$temperature),
    as.numeric(imd_temp_code(df$longitude, df$latitude, day))
  )
  expect_equal(range(df$longitude), c(67.5, 97.5))
  expect_equal(range(df$latitude), c(7.5, 37.5))
  expect_true(all(df$longitude %% 1 == 0.5 & df$latitude %% 1 == 0.5))
})

test_that("read_imd_temperature drops 99.9 and NaN cells on every day", {
  df <- suppressMessages(read_imd_temperature(temp_2023, "tmin", 2023))
  i <- cell_index(df)
  expect_false(any(imd_is_sea(i$ilon, i$ilat)))
  expect_false(any(i$ilon == imd_nan_cell[1] & i$ilat == imd_nan_cell[2]))
  expect_false(anyNA(df$temperature))
  per_day <- table(df$date)
  expect_length(per_day, 365L)
  expect_true(all(per_day == n_temp_land()))
})

test_that("read_imd_temperature maps day 60 of a leap year to 29 February", {
  f <- write_full_temperature(tempfile(fileext = ".grd"), 2000) # divisible by 400: leap
  df <- suppressMessages(read_imd_temperature(f, "tmax", 2000))
  expect_equal(length(unique(df$date)), 366L)
  cell <- df[df$longitude == 77.5 & df$latitude == 29.5, ]
  expect_equal(cell$temperature[cell$date == as.Date("2000-02-29")], imd_temp_code(77.5, 29.5, 60))
  expect_equal(cell$temperature[cell$date == as.Date("2000-12-31")], imd_temp_code(77.5, 29.5, 366))
})

test_that("read_imd_temperature treats 1900 and 2100 as common years", {
  expect_equal(is_leap_year(c(1900, 2000, 2023, 2024, 2100)), c(FALSE, TRUE, FALSE, TRUE, FALSE))
  f <- write_full_temperature(tempfile(fileext = ".grd"), 2100)
  df <- suppressMessages(read_imd_temperature(f, "tmax", 2100))
  expect_equal(length(unique(df$date)), 365L)
})

test_that("read_imd_temperature warns when a leap-year file has only 365 days", {
  expect_warning(suppressMessages(read_imd_temperature(temp_2023, "tmax", 2024)), "Expected")
})

test_that("read_imd_temperature reads little-endian float32 only", {
  f <- tempfile(fileext = ".grd")
  con <- file(f, "wb")
  writeBin(rep(25, 31 * 31 * 365), con, size = 4, endian = "big")
  close(con)
  df <- suppressMessages(read_imd_temperature(f, "tmax", 2023))
  # big-endian 25.0 read as little-endian is not a plausible temperature
  expect_false(isTRUE(all(df$temperature == 25)))
})

# ---- rainfall reader ------------------------------------------------------

rain_lons <- seq(72, 74, by = 0.25)
rain_lats <- seq(18, 19.5, by = 0.25)

# Read through the stars route or, with stars failing, the ncdf4 fallback.
read_rain_with <- function(reader, f, year) {
  if (reader == "ncdf4") local_mocked_bindings(read_ncdf = function(...) stop("no stars"))
  suppressWarnings(suppressMessages(read_imd_rainfall(f, 0.25, year)))
}

# imd_fx_write_rainfall() stores 100 * lon_i + 10 * lat_i + day; cell (1, 1) is missing
check_rain_frame <- function(df, year, lons = rain_lons, lats = rain_lats) {
  expect_equal(nrow(df), (length(lons) * length(lats) - 1L) * days_in_year(year))
  day <- as.integer(df$date - as.Date(sprintf("%d-01-01", year))) + 1L
  expect_equal(df$rainfall, imd_fx_rain_value(match(df$longitude, lons), match(df$latitude, lats), day))
  expect_false(any(df$longitude == lons[1] & df$latitude == lats[1]))
  expect_equal(range(df$date), as.Date(sprintf(c("%d-01-01", "%d-12-31"), year)))
}

test_that("both rainfall readers place every cell and day", {
  for (reader in c("stars", "ncdf4")) {
    for (year in c(2023, 2024)) {
      f <- imd_fx_write_rainfall(tempfile(fileext = ".nc"), year, rain_lons, rain_lats)
      check_rain_frame(read_rain_with(reader, f, year), year)
    }
  }
})

test_that("both rainfall readers handle latitude stored north to south", {
  lats <- rev(rain_lats)
  f <- imd_fx_write_rainfall(tempfile(fileext = ".nc"), 2023, rain_lons, lats)
  for (reader in c("stars", "ncdf4")) check_rain_frame(read_rain_with(reader, f, 2023), 2023, lats = lats)
})

test_that("zero rainfall is kept and only the -999 fill is dropped", {
  f <- tempfile(fileext = ".nc")
  dims <- list(
    ncdf4::ncdim_def("lon", "degrees_east", c(75, 75.25)),
    ncdf4::ncdim_def("lat", "degrees_north", 20),
    ncdf4::ncdim_def("time", "days since 2023-01-01", 0:364, calendar = "standard")
  )
  var <- ncdf4::ncvar_def("rf", "mm", dims, missval = -999, prec = "float")
  nc <- ncdf4::nc_create(f, list(var))
  v <- matrix(0, 2, 365)
  v[2, ] <- -999
  v[1, 100] <- 0.5
  ncdf4::ncvar_put(nc, var, v)
  ncdf4::nc_close(nc)
  df <- suppressMessages(read_imd_rainfall(f, 0.25, 2023))
  expect_equal(nrow(df), 365L)
  expect_equal(sum(df$rainfall == 0), 364L)
  expect_equal(unique(df$longitude), 75)
})

# ---- multi-year processing ------------------------------------------------

test_that("process_imd_files stacks years with continuous dates", {
  dir <- withr::local_tempdir()
  files <- file.path(dir, sprintf("imd_tmax_1.0_%d.grd", 2023:2024))
  write_full_temperature(files[1], 2023)
  write_full_temperature(files[2], 2024)
  df <- suppressMessages(process_imd_files(files, "tmax"))
  expect_equal(length(unique(df$date)), 365L + 366L)
  expect_equal(nrow(df), n_temp_land() * (365L + 366L))
  expect_false(is.unsorted(df$date))
  expect_equal(diff(sort(unique(df$date))), rep(as.difftime(1, units = "days"), 730))
})

# ---- spatial filters ------------------------------------------------------

grid_frame <- function() {
  g <- expand.grid(longitude = seq(67.5, 97.5, 1), latitude = seq(7.5, 37.5, 1))
  data.frame(date = as.Date("2023-05-01"), g, temperature = seq_len(nrow(g)))
}

test_that("filter_imd_by_bbox matches a direct subset for many boxes", {
  d <- grid_frame()
  set.seed(42)
  for (i in 1:25) {
    lat <- sort(runif(2, 6, 39))
    lon <- sort(runif(2, 66, 99))
    got <- suppressMessages(filter_imd_by_bbox(d, lat[2], lat[1], lon[2], lon[1]))
    want <- d[d$latitude >= lat[1] & d$latitude <= lat[2] & d$longitude >= lon[1] & d$longitude <= lon[2], ]
    expect_equal(got, want)
  }
})

test_that("filter_imd_by_bbox includes cells on the box edges", {
  d <- grid_frame()
  got <- suppressMessages(filter_imd_by_bbox(d, north = 30.5, south = 28.5, east = 78.5, west = 76.5))
  expect_equal(nrow(got), 9L)
  expect_setequal(unique(got$latitude), c(28.5, 29.5, 30.5))
  expect_setequal(unique(got$longitude), c(76.5, 77.5, 78.5))
})

test_that("filter_imd_by_bbox returns zero rows for a box between cell centres", {
  d <- grid_frame()
  got <- suppressMessages(filter_imd_by_bbox(d, north = 28.9, south = 28.6, east = 77.9, west = 77.6))
  expect_equal(nrow(got), 0L)
  expect_named(got, names(d))
})

test_that("filter_imd_by_geojson agrees with the bbox filter for a rectangle", {
  skip_if_not_installed("sf")
  d <- grid_frame()
  f <- tempfile(fileext = ".geojson")
  imd_fx_write_geojson(f, xmin = 72.2, ymin = 18.2, xmax = 80.8, ymax = 25.8)
  a <- suppressMessages(filter_imd_by_geojson(d, f))
  b <- suppressMessages(filter_imd_by_bbox(d, north = 25.8, south = 18.2, east = 80.8, west = 72.2))
  expect_equal(a, b)
  expect_equal(nrow(a), 9L * 8L)
})

# ---- temporal aggregation -------------------------------------------------

daily_frame <- function(value, years = 2023:2024, cells = data.frame(longitude = c(72.5, 80.5), latitude = c(19.5, 28.5))) {
  dates <- seq(as.Date(sprintf("%d-01-01", min(years))), as.Date(sprintf("%d-12-31", max(years))), by = "day")
  d <- merge(data.frame(date = dates), cells)
  set.seed(7)
  d[[value]] <- round(runif(nrow(d), 0, 40), 1)
  d[order(d$date, d$latitude, d$longitude), ]
}

test_that("monthly rainfall is the exact sum of each month's days", {
  d <- daily_frame("rainfall")
  m <- suppressMessages(aggregate_imd_by_frequency(d, "monthly"))
  expect_equal(nrow(m), 24L * 2L)
  want <- stats::aggregate(rainfall ~ format(date, "%Y-%m") + latitude + longitude, data = d, FUN = sum)
  names(want)[1] <- "ym"
  m$ym <- format(m$date, "%Y-%m")
  both <- merge(m, want, by = c("ym", "latitude", "longitude"))
  expect_equal(nrow(both), 48L)
  expect_equal(both$rainfall.x, both$rainfall.y, tolerance = 1e-10)
  expect_true(all(format(m$date, "%d") == "01"))
})

test_that("yearly rainfall equals the sum of its monthly totals", {
  d <- daily_frame("rainfall")
  m <- suppressMessages(aggregate_imd_by_frequency(d, "monthly"))
  y <- suppressMessages(aggregate_imd_by_frequency(d, "yearly"))
  m$year <- format(m$date, "%Y")
  from_months <- stats::aggregate(rainfall ~ year + latitude + longitude, data = m, FUN = sum)
  y$year <- format(y$date, "%Y")
  both <- merge(y, from_months, by = c("year", "latitude", "longitude"))
  expect_equal(both$rainfall.x, both$rainfall.y, tolerance = 1e-10)
  expect_equal(sort(unique(y$date)), as.Date(c("2023-01-01", "2024-01-01")))
})

test_that("yearly temperature is the mean of days, not of monthly means", {
  d <- daily_frame("temperature", years = 2024)
  y <- suppressMessages(aggregate_imd_by_frequency(d, "yearly"))
  cell <- d$longitude == 72.5
  expect_equal(y$temperature[y$longitude == 72.5], mean(d$temperature[cell]))
  m <- suppressMessages(aggregate_imd_by_frequency(d, "monthly"))
  mean_of_months <- mean(m$temperature[m$longitude == 72.5])
  expect_false(isTRUE(all.equal(mean_of_months, mean(d$temperature[cell]))))
})

test_that("monthly temperature means use 29 days in a leap February", {
  d <- daily_frame("temperature", years = 2024)
  m <- suppressMessages(aggregate_imd_by_frequency(d, "monthly"))
  feb <- d$longitude == 80.5 & format(d$date, "%m") == "02"
  expect_equal(sum(feb), 29L)
  expect_equal(
    m$temperature[m$longitude == 80.5 & m$date == as.Date("2024-02-01")],
    mean(d$temperature[feb])
  )
})

test_that("aggregation skips missing values and is case-insensitive", {
  d <- daily_frame("rainfall", years = 2023)
  d$rainfall[d$date == as.Date("2023-03-15")] <- NA
  m <- suppressMessages(aggregate_imd_by_frequency(d, "Monthly"))
  mar <- d$longitude == 72.5 & format(d$date, "%m") == "03"
  expect_equal(m$rainfall[m$longitude == 72.5 & m$date == as.Date("2023-03-01")], sum(d$rainfall[mar], na.rm = TRUE))
  expect_identical(suppressMessages(aggregate_imd_by_frequency(d, "DAILY")), d)
})

test_that("aggregating an empty selection returns no rows", {
  d <- daily_frame("rainfall")[0, ]
  for (f in c("monthly", "yearly")) {
    a <- suppressMessages(aggregate_imd_by_frequency(d, f))
    expect_equal(nrow(a), 0L)
    expect_named(a, c("date", "latitude", "longitude", "rainfall"))
  }
})

test_that("aggregation preserves totals over the whole record", {
  d <- daily_frame("rainfall")
  for (f in c("monthly", "yearly")) {
    a <- suppressMessages(aggregate_imd_by_frequency(d, f))
    expect_equal(sum(a$rainfall), sum(d$rainfall), tolerance = 1e-10)
  }
})

# ---- end-to-end pipelines -------------------------------------------------

test_that("imd_temperature_bbox daily output equals reader + filter", {
  imd_fx_mock_temp_download(write_full_temperature)
  out <- withr::local_tempdir()
  res <- suppressMessages(imd_temperature_bbox("hw", 2023, 2024,
    north = 30, south = 26, east = 80, west = 75, var_type = "tmax", output_dir = out
  ))
  day <- as.integer(res$date - as.Date(paste0(format(res$date, "%Y"), "-01-01"))) + 1L
  expect_identical(as.numeric(res$temperature), as.numeric(imd_temp_code(res$longitude, res$latitude, day)))
  expect_true(all(res$latitude >= 26 & res$latitude <= 30 & res$longitude >= 75 & res$longitude <= 80))
  cells <- unique(res[, c("longitude", "latitude")])
  i <- cell_index(cells)
  expect_equal(nrow(cells), sum(!imd_is_sea(rep(9:13, 4), rep(20:23, each = 5))))
  expect_equal(nrow(res), nrow(cells) * (365L + 366L))
  expect_false(any(imd_is_sea(i$ilon, i$ilat)))
})

test_that("imd_temperature_bbox monthly output averages the daily values", {
  imd_fx_mock_temp_download(write_full_temperature)
  out <- withr::local_tempdir()
  args <- list("m", 2024, 2024, north = 30, south = 28, east = 79, west = 77, var_type = "tmin", output_dir = out)
  daily <- suppressMessages(do.call(imd_temperature_bbox, args))
  monthly <- suppressMessages(do.call(imd_temperature_bbox, c(args, frequency = "monthly")))
  expect_equal(length(unique(monthly$date)), 12L)
  expect_gte(length(unique(paste(daily$longitude, daily$latitude))), 3L)
  for (cell in split(daily, list(daily$longitude, daily$latitude), drop = TRUE)) {
    want <- tapply(cell$temperature, format(cell$date, "%m"), mean)
    got <- monthly[monthly$longitude == cell$longitude[1] & monthly$latitude == cell$latitude[1], ]
    expect_equal(got$temperature, as.numeric(want), tolerance = 1e-12)
  }
})

test_that("imd_temperature_geojson matches the bbox route for the same rectangle", {
  skip_if_not_installed("sf")
  imd_fx_mock_temp_download(write_full_temperature)
  out <- withr::local_tempdir()
  f <- file.path(out, "r.geojson")
  imd_fx_write_geojson(f, xmin = 75, ymin = 26, xmax = 80, ymax = 30)
  a <- suppressMessages(imd_temperature_geojson("g", 2023, 2023, f, var_type = "tmax", output_dir = out))
  b <- suppressMessages(imd_temperature_bbox("b", 2023, 2023, 30, 26, 80, 75, var_type = "tmax", output_dir = out))
  key <- function(d) d[order(d$date, d$latitude, d$longitude), ]
  expect_equal(key(a), key(b), ignore_attr = TRUE)
})

# ---- IMD heatwave thresholds ----------------------------------------------

hw_dates <- seq(as.Date("2001-01-01"), as.Date("2003-12-31"), by = "day")

test_that("IMD severe heatwave starts strictly above a 6.4 C departure", {
  tmax <- rep(38, length(hw_dates))
  i <- which(hw_dates == as.Date("2003-05-01"))
  tmax[i + 0:1] <- 38 + 6.4 # heatwave, not severe
  tmax[i + 10:11] <- 38 + 6.5 # severe
  r <- heatwave_days(hw_dates, tmax, baseline = c(2001, 2002))
  expect_equal(sum(r$day), 4L)
  expect_equal(r$date[r$severe], hw_dates[i + 10:11])
})

test_that("IMD normals use a +/- 2 day calendar window that wraps the year end", {
  # baseline Tmax 30 C, except 30 December to 3 January at 35 C, so the
  # 1 January normal pools only hot days and 4 January pools three cool ones
  tmax <- rep(30, length(hw_dates))
  md <- format(hw_dates, "%m-%d")
  base <- hw_dates < as.Date("2003-01-01")
  tmax[base & md %in% c("12-30", "12-31", "01-01", "01-02", "01-03")] <- 35
  tmax[!base] <- 0
  jan <- hw_dates %in% as.Date(c("2003-01-01", "2003-01-02", "2003-01-04", "2003-01-05"))
  tmax[jan] <- 39.5
  r <- heatwave_days(hw_dates, tmax, baseline = c(2001, 2002), terrain = "hilly")
  # normals: 1 Jan 35, 2 Jan 34, 4 Jan 32, 5 Jan 31; severe needs > 6.4
  expect_equal(r$date[r$day], hw_dates[jan])
  expect_equal(r$date[r$severe], as.Date(c("2003-01-04", "2003-01-05")))
})

test_that("IMD plains floor is inclusive at exactly 40 C", {
  tmax <- rep(35.5, length(hw_dates))
  i <- which(hw_dates == as.Date("2003-05-01"))
  tmax[i + 0:1] <- 40 # departure exactly 4.5
  tmax[i + 10:11] <- 39.99
  r <- heatwave_days(hw_dates, tmax, baseline = c(2001, 2002))
  expect_equal(r$date[r$day], hw_dates[i + 0:1])
})
