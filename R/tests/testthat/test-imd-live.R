# Live tests against the IMD Pune server (about 35 MB of downloads). They run
# only with VARUNAYAN_LIVE_TESTS=true and never on CRAN.

live_dir <- function() {
  d <- file.path(tempdir(), "imd-live")
  dir.create(d, showWarnings = FALSE)
  d
}

# downloads land in the session cache (setup.R), so each file is fetched once
live_temp <- function(var, year) {
  suppressMessages(download_imd_temperature(year, year, var, output_dir = live_dir()))
}
live_rain <- function(resolution, year) {
  suppressMessages(download_imd_rainfall(year, year, resolution, output_dir = live_dir()))
}
read_temp <- function(var, year) {
  data.table::as.data.table(suppressMessages(read_imd_temperature(live_temp(var, year), var, year)))
}
read_rain <- function(resolution, year) {
  data.table::as.data.table(suppressMessages(read_imd_rainfall(live_rain(resolution, year), resolution, year)))
}
cell <- function(d, lat, lon) d[d$latitude == lat & d$longitude == lon, ]
monthly_mean <- function(d) tapply(d[[ncol(d)]], as.integer(format(d$date, "%m")), mean)
area_mean <- function(totals) stats::weighted.mean(totals$total, cos(totals$latitude * pi / 180))

# Server and download layer ----------------------------------------------------

test_that("the IMD server answers", {
  skip_live_imd()
  expect_true(check_imd_server())
})

test_that("temperature files hold 31 x 31 float32 values for every day of the year", {
  skip_live_imd()
  expect_equal(file.size(live_temp("tmax", 2019)), 31 * 31 * 365 * 4)
  expect_equal(file.size(live_temp("tmin", 2019)), 31 * 31 * 365 * 4)
  expect_equal(file.size(live_temp("tmax", 2020)), 31 * 31 * 366 * 4)
})

test_that("rainfall NetCDF grids match get_imd_grid_specs()", {
  skip_live_imd()
  for (res in c(0.25, 1.0)) {
    spec <- get_imd_grid_specs(paste0("rainfall_", format(res, nsmall = 1)))
    nc <- ncdf4::nc_open(live_rain(res, 2019))
    lon <- as.vector(ncdf4::ncvar_get(nc, "LONGITUDE"))
    lat <- as.vector(ncdf4::ncvar_get(nc, "LATITUDE"))
    vars <- names(nc$var)
    missval <- nc$var[[spec$variable_name]]$missval
    ncdf4::nc_close(nc)
    expect_equal(vars, spec$variable_name)
    expect_equal(missval, spec$missing_value)
    expect_equal(length(lon), spec$nlon)
    expect_equal(length(lat), spec$nlat)
    expect_equal(range(lon), c(spec$lon_start, spec$lon_end))
    expect_equal(range(lat), c(spec$lat_start, spec$lat_end))
    expect_equal(unique(round(diff(lon), 6)), res)
    expect_equal(unique(round(diff(lat), 6)), res)
  }
})

test_that("list_imd_datasets() grid sizes match the files", {
  skip_live_imd()
  ds <- list_imd_datasets()
  for (id in ds$dataset_id) {
    spec <- get_imd_grid_specs(id)
    expect_equal(ds$grid_size[ds$dataset_id == id], paste0(spec$nlon, "x", spec$nlat))
  }
})

test_that("the first and last advertised years download", {
  skip_live_imd()
  ds <- list_imd_datasets()
  first <- function(id) ds$year_start[ds$dataset_id == id]
  last <- function(id) ds$year_end[ds$dataset_id == id]
  temp_bytes <- function(y) 31 * 31 * days_in_year(y) * 4
  expect_equal(file.size(live_temp("tmax", last("tmax_1.0"))), temp_bytes(last("tmax_1.0")))
  expect_equal(file.size(live_temp("tmin", first("tmin_1.0"))), temp_bytes(first("tmin_1.0")))
  expect_equal(length(unique(read_rain(1.0, last("rainfall_1.0"))$date)), days_in_year(last("rainfall_1.0")))
  expect_equal(length(unique(read_rain(1.0, first("rainfall_1.0"))$date)), days_in_year(first("rainfall_1.0")))
  # the 0.25 degree files are large, so count days from the time axis; the
  # first year is covered by the form test below
  y <- last("rainfall_0.25")
  nc <- ncdf4::nc_open(live_rain(0.25, y))
  on.exit(ncdf4::nc_close(nc))
  expect_equal(nc$dim[[grep("time", names(nc$dim), ignore.case = TRUE)]]$len, days_in_year(y))
})

test_that("every gridded data page posts the form and years the package uses", {
  skip_live_imd()
  ds <- list_imd_datasets()
  for (i in seq_len(nrow(.IMD_ENDPOINTS))) {
    e <- .IMD_ENDPOINTS[i, ]
    r <- suppressWarnings(.imd_request(httr::GET, paste0(.IMD_GRID_URL, e$page), timeout_s = 120))
    expect_equal(httr::status_code(r), 200, info = e$page)
    html <- httr::content(r, "text", encoding = "UTF-8")
    expect_match(html, sprintf('action="%s"', e$php), fixed = TRUE, info = e$page)
    expect_match(html, sprintf('<select[^>]*name="%s"', e$param), info = e$page)
    years <- as.integer(gsub("\\D", "", regmatches(html, gregexpr('value= ?"[0-9]{4}"', html))[[1]]))
    advertised <- ds[ds$dataset_id == e$dataset, ]
    expect_equal(sort(years), advertised$year_start:advertised$year_end, info = e$page)
  }
})

test_that("a year before the archive starts returns no data", {
  skip_live_imd()
  e <- .imd_endpoint("tmax_1.0")
  expect_error(
    suppressWarnings(download_imd_year(1950, e$php, e$param, .IMD_GRID_URL, file.path(live_dir(), "tmax_1950.grd"))),
    "HTML|empty"
  )
})

test_that("a cached year is served without contacting the server", {
  skip_live_imd()
  first <- live_temp("tmax", 2019)
  local_mocked_bindings(
    download_imd_year = function(...) stop("network used"),
    check_imd_server = function(...) stop("network used")
  )
  again <- suppressMessages(download_imd_temperature(2019, 2019, "tmax", output_dir = tempfile("cached")))
  expect_equal(unname(tools::md5sum(again)), unname(tools::md5sum(first)))
})

# Temperature reader on real files ---------------------------------------------

test_that("read_imd_temperature() returns a tidy year of valid values", {
  skip_live_imd()
  for (year in c(2019, 2020)) {
    d <- read_temp("tmax", year)
    expect_equal(names(d), c("date", "latitude", "longitude", "temperature"))
    expect_s3_class(d$date, "Date")
    expect_equal(sort(unique(d$date)), seq(as.Date(paste0(year, "-01-01")), as.Date(paste0(year, "-12-31")), by = "day"))
    expect_false(anyNA(d$temperature))
    expect_true(all(d$temperature < 99)) # 99.9 marks missing
    expect_true(all(d$latitude %in% seq(7.5, 37.5, by = 1)))
    expect_true(all(d$longitude %in% seq(67.5, 97.5, by = 1)))
    expect_false(anyDuplicated(d[, c("date", "latitude", "longitude")]) > 0)
  }
  expect_true(as.Date("2020-02-29") %in% read_temp("tmax", 2020)$date)
})

test_that("temperatures stay below India's highest recorded temperature", {
  skip_live_imd()
  # 51.0 C at Phalodi, 19 May 2016 (IMD); a 1 degree grid average cannot exceed it
  expect_lt(max(read_temp("tmax", 2019)$temperature), 51)
  expect_lt(max(read_temp("tmin", 2019)$temperature), max(read_temp("tmax", 2019)$temperature))
})

test_that("land cells have data and sea cells are masked", {
  skip_live_imd()
  d <- read_temp("tmax", 2019)
  expect_equal(nrow(cell(d, 28.5, 77.5)), 365) # Delhi
  expect_equal(nrow(cell(d, 13.5, 80.5)), 365) # Chennai
  expect_equal(nrow(cell(d, 15.5, 67.5)), 0) # Arabian Sea
  expect_equal(nrow(cell(d, 15.5, 88.5)), 0) # Bay of Bengal
})

test_that("the grid is oriented: Delhi's seasonal cycle is larger than Chennai's", {
  skip_live_imd()
  d <- read_temp("tmax", 2019)
  delhi <- monthly_mean(cell(d, 28.5, 77.5)[, c("date", "temperature")])
  chennai <- monthly_mean(cell(d, 13.5, 80.5)[, c("date", "temperature")])
  expect_gt(delhi[["5"]], delhi[["1"]] + 10) # May far hotter than January in the north
  expect_lt(delhi[["1"]], chennai[["1"]]) # January warmer in the south
  expect_gt(diff(range(delhi)), diff(range(chennai)))
})

test_that("independently gridded tmin rarely exceeds tmax", {
  skip_live_imd()
  m <- merge(read_temp("tmax", 2019), read_temp("tmin", 2019), by = c("date", "latitude", "longitude"))
  expect_gt(nrow(m), 300 * 365)
  # a swapped or misaligned file would invert most days
  expect_lt(mean(m$temperature.y > m$temperature.x), 0.001)
  expect_gt(mean(m$temperature.x - m$temperature.y), 5)
})

# Rainfall reader on real files ------------------------------------------------

test_that("read_imd_rainfall() returns a tidy year of valid values at both resolutions", {
  skip_live_imd()
  for (res in c(0.25, 1.0)) {
    d <- read_rain(res, 2019)
    spec <- get_imd_grid_specs(paste0("rainfall_", format(res, nsmall = 1)))
    expect_equal(names(d), c("date", "latitude", "longitude", "rainfall"))
    expect_s3_class(d$date, "Date")
    expect_equal(sort(unique(d$date)), seq(as.Date("2019-01-01"), as.Date("2019-12-31"), by = "day"))
    expect_true(all(d$rainfall >= 0)) # -999 marks missing
    expect_true(all(d$latitude %in% seq(spec$lat_start, spec$lat_end, by = res)))
    expect_true(all(d$longitude %in% seq(spec$lon_start, spec$lon_end, by = res)))
    expect_false(anyDuplicated(d[, c("date", "latitude", "longitude")]) > 0)
    expect_equal(length(unique(d[, .N, by = date]$N)), 1) # same land mask every day
  }
})

test_that("rainfall is masked over the sea and highest in the northeast", {
  skip_live_imd()
  d <- read_rain(0.25, 2019)
  expect_equal(nrow(cell(d, 15, 70)), 0) # Arabian Sea
  annual <- d[, .(total = sum(rainfall)), by = .(latitude, longitude)]
  cherrapunji <- annual[latitude == 25.25 & longitude == 91.75, total]
  jaisalmer <- annual[latitude == 27 & longitude == 70.75, total]
  expect_gt(cherrapunji, 10 * jaisalmer)
})

test_that("2019 monsoon rainfall over India is 110% of the 88 cm long period average", {
  skip_live_imd()
  # IMD end-of-season press release, 30 September 2019: June-September rainfall
  # was 110% of the 1961-2010 long period average of 88 cm.
  d <- read_rain(0.25, 2019)
  jjas <- d[as.integer(format(date, "%m")) %in% 6:9, .(total = sum(rainfall)), by = .(latitude, longitude)]
  expect_equal(round(100 * area_mean(jjas) / 880), 110)
  annual <- d[, .(total = sum(rainfall)), by = .(latitude, longitude)]
  expect_gt(area_mean(jjas) / area_mean(annual), 0.5) # most rain falls in the monsoon
})

test_that("1.0 and 0.25 degree rainfall agree on the all-India monsoon total", {
  skip_live_imd()
  jjas <- function(d) area_mean(d[as.integer(format(date, "%m")) %in% 6:9, .(total = sum(rainfall)), by = .(latitude, longitude)])
  expect_equal(jjas(read_rain(1.0, 2019)), jjas(read_rain(0.25, 2019)), tolerance = 0.1)
})

# End-to-end entry points ------------------------------------------------------

test_that("imd_temperature_bbox() matches the reader, cropped and averaged by month", {
  skip_live_imd()
  out <- tempfile("bbox")
  res <- suppressMessages(imd_temperature_bbox("delhi", 2019, 2019,
    north = 29, south = 28, east = 78, west = 76,
    var_type = "tmax", frequency = "monthly", output_dir = out
  ))
  expect_equal(names(res), c("date", "latitude", "longitude", "temperature"))
  expect_true(all(res$latitude >= 28 & res$latitude <= 29 & res$longitude >= 76 & res$longitude <= 78))
  expect_equal(sort(unique(res$date)), seq(as.Date("2019-01-01"), by = "month", length.out = 12))
  daily <- cell(read_temp("tmax", 2019), 28.5, 77.5)
  expect_equal(
    cell(res, 28.5, 77.5)$temperature,
    unname(as.vector(monthly_mean(daily[, c("date", "temperature")]))),
    tolerance = 1e-6
  )
  csv <- file.path(out, "delhi_imd_output", "delhi_imd_tmax_1_monthly_data.csv")
  expect_true(file.exists(csv))
  expect_equal(nrow(utils::read.csv(csv)), nrow(res))
  expect_false(file.exists(file.path(out, "imd_tmax_1.0_2019.grd"))) # save_raw = FALSE
})

test_that("imd_rainfall_bbox() yearly totals equal the summed daily values", {
  skip_live_imd()
  res <- suppressMessages(imd_rainfall_bbox("mh", 2019, 2019,
    north = 20, south = 18, east = 75, west = 73,
    resolution = 1.0, frequency = "yearly", output_dir = tempfile("bbox")
  ))
  expect_equal(unique(res$date), as.Date("2019-01-01"))
  daily <- read_rain(1.0, 2019)[latitude >= 18 & latitude <= 20 & longitude >= 73 & longitude <= 75]
  manual <- daily[, .(rainfall = sum(rainfall)), by = .(latitude, longitude)]
  both <- merge(as.data.frame(res), manual, by = c("latitude", "longitude"))
  expect_equal(nrow(both), nrow(manual))
  expect_equal(both$rainfall.x, both$rainfall.y, tolerance = 1e-6)
})

test_that("imd_rainfall_geojson() keeps exactly the land cells of the polygon", {
  skip_live_imd()
  region <- system.file("extdata", "region.geojson", package = "varunayan")
  res <- suppressMessages(imd_rainfall_geojson("region", 2019, 2019, region,
    resolution = 0.25, frequency = "monthly", output_dir = tempfile("geo")
  ))
  expect_gt(nrow(res), 0)
  expect_true(all(res$latitude >= 18 & res$latitude <= 22 & res$longitude >= 72 & res$longitude <= 78))
  expect_equal(length(unique(res$date)), 12)
  # the 0.25 degree grid has points on all four edges; each edge is kept
  expect_true(all(c(18, 22) %in% res$latitude) && all(c(72, 78) %in% res$longitude))
  inside <- unique(read_rain(0.25, 2019)[latitude >= 18 & latitude <= 22 & longitude >= 72 & longitude <= 78, .(latitude, longitude)])
  expect_equal(nrow(unique(res[, c("latitude", "longitude")])), nrow(inside))
})

test_that("imd_temperature_geojson() agrees with the bbox route for a rectangle", {
  skip_live_imd()
  region <- system.file("extdata", "region.geojson", package = "varunayan")
  geo <- suppressMessages(imd_temperature_geojson("geo", 2019, 2019, region,
    var_type = "tmin", frequency = "yearly", output_dir = tempfile("geo")
  ))
  box <- suppressMessages(imd_temperature_bbox("box", 2019, 2019,
    north = 22, south = 18, east = 78, west = 72,
    var_type = "tmin", frequency = "yearly", output_dir = tempfile("box")
  ))
  # grid points sit at x.5, never on the polygon edge
  key <- function(d) d[order(d$latitude, d$longitude), c("latitude", "longitude", "temperature")]
  expect_equal(key(geo), key(box), ignore_attr = TRUE)
})

test_that("PascalCase aliases return the same data", {
  skip_live_imd()
  args <- list("alias", 2019, 2019, north = 29, south = 28, east = 78, west = 76, var_type = "tmax", frequency = "yearly")
  a <- suppressMessages(do.call(imd_temperature_bbox, c(args, output_dir = tempfile("a"))))
  b <- suppressMessages(do.call(IMDTemperatureBbox, c(args, output_dir = tempfile("b"))))
  expect_equal(a, b)
})

test_that("imd_exposure_bbox() summarises real IMD temperatures", {
  skip_live_imd()
  res <- suppressMessages(imd_exposure_bbox(2020, 2020,
    north = 29, south = 28, east = 78, west = 76,
    baseline = c(2019, 2020), output_dir = tempfile("exp")
  ))
  expect_true(all(res$year == 2020))
  expect_true(all(res$n_days == 366))
  delhi <- res[res$latitude == 28.5 & res$longitude == 77.5, ]
  expect_equal(nrow(delhi), 1)
  expect_equal(delhi$tmax_mean, mean(cell(read_temp("tmax", 2020), 28.5, 77.5)$temperature), tolerance = 1e-6)
  expect_equal(delhi$dtr_mean, delhi$tmax_mean - delhi$tmin_mean, tolerance = 1e-6)
  expect_true(all(res$heatwave_days >= 0 & res$heatwave_days <= res$n_days))
})
