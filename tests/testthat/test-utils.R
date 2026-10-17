test_that("is_valid_geojson works correctly", {
  # Valid GeoJSON examples
  valid_feature <- list(
    type = "Feature",
    geometry = list(
      type = "Point",
      coordinates = c(-74.0060, 40.7128)
    ),
    properties = list()
  )
  expect_true(is_valid_geojson(valid_feature))

  valid_collection <- list(
    type = "FeatureCollection",
    features = list(valid_feature)
  )
  expect_true(is_valid_geojson(valid_collection))

  # Invalid examples
  expect_false(is_valid_geojson(list(invalid = "data")))
  expect_false(is_valid_geojson("not a list"))
  expect_false(is_valid_geojson(list(type = "InvalidType")))
})

test_that("create_geojson_from_bbox creates valid GeoJSON", {
  geojson <- create_geojson_from_bbox(40, 35, -70, -75)

  expect_true(is_valid_geojson(geojson))
  expect_equal(geojson$type, "Feature")
  expect_equal(geojson$geometry$type, "Polygon")
  expect_length(geojson$geometry$coordinates[[1]], 5) # 5 points for closed polygon

  # Check coordinates are correct
  coords <- geojson$geometry$coordinates[[1]]
  expect_equal(coords[[1]], c(-75, 35)) # SW corner
  expect_equal(coords[[3]], c(-70, 40)) # NE corner
})

test_that("validate_coordinates works correctly", {
  expect_true(validate_coordinates(40.7128, -74.0060)) # NYC
  expect_true(validate_coordinates(0, 0)) # Equator/Prime Meridian
  expect_true(validate_coordinates(-90, -180)) # Extreme valid values
  expect_true(validate_coordinates(90, 180)) # Extreme valid values

  expect_false(validate_coordinates(91, 0)) # Invalid latitude
  expect_false(validate_coordinates(-91, 0)) # Invalid latitude
  expect_false(validate_coordinates(0, 181)) # Invalid longitude
  expect_false(validate_coordinates(0, -181)) # Invalid longitude
  expect_false(validate_coordinates(NA, 0)) # NA values
  expect_false(validate_coordinates(0, NA)) # NA values
})

test_that("validate_bbox works correctly", {
  expect_true(validate_bbox(40, 35, -70, -75)) # Valid bbox
  expect_false(validate_bbox(35, 40, -70, -75)) # North < South
  expect_false(validate_bbox(40, 35, -75, -70)) # East < West
  expect_false(validate_bbox(91, 35, -70, -75)) # Invalid north
  expect_false(validate_bbox(40, -91, -70, -75)) # Invalid south
})

test_that("format_pressure_levels works correctly", {
  expect_null(format_pressure_levels(NULL))

  numeric_levels <- c(1000, 850, 500)
  char_levels <- format_pressure_levels(numeric_levels)
  expect_type(char_levels, "character")
  expect_equal(char_levels, c("1000", "850", "500"))

  # Already character
  expect_equal(format_pressure_levels(c("1000", "850")), c("1000", "850"))
})

test_that("format_date_range works correctly", {
  start_date <- as.Date("2023-01-01")
  end_date <- as.Date("2023-01-03")

  date_range <- format_date_range(start_date, end_date)
  expected <- c("2023-01-01", "2023-01-02", "2023-01-03")

  expect_equal(date_range, expected)
  expect_type(date_range, "character")
})

test_that("get_time_values works correctly", {
  hourly_times <- get_time_values("hourly")
  expect_length(hourly_times, 24)
  expect_equal(hourly_times[1], "00:00")
  expect_equal(hourly_times[24], "23:00")

  daily_times <- get_time_values("daily")
  expect_equal(daily_times, "12:00")

  monthly_times <- get_time_values("monthly")
  expect_equal(monthly_times, "12:00")
})

test_that("create_temp_geojson_file creates file", {
  geojson_data <- list(
    type = "Feature",
    geometry = list(type = "Point", coordinates = c(0, 0)),
    properties = list()
  )

  temp_file <- create_temp_geojson_file(geojson_data, "test")

  expect_true(file.exists(temp_file))
  expect_true(grepl("\\.geojson$", temp_file))
  expect_true(grepl("varunayan_test_", basename(temp_file)))

  # Check content
  read_data <- jsonlite::fromJSON(temp_file)
  expect_equal(read_data$type, "Feature")

  # Clean up
  unlink(temp_file)
})

test_that("is_valid_geojson accepts all geometry types", {
  for (type in c(
    "Polygon", "MultiPolygon", "Point", "MultiPoint", "LineString",
    "MultiLineString", "GeometryCollection"
  )) {
    expect_true(is_valid_geojson(list(type = type)), info = type)
  }
  expect_false(is_valid_geojson(list(type = "feature")))
  expect_false(is_valid_geojson(NULL))
})

test_that("convert_to_geojson builds a point FeatureCollection", {
  df <- data.frame(lon = c(77.1, 72.8), lat = c(28.6, 19.1), city = c("Delhi", "Mumbai"), pop = c(1, 2))
  gj <- convert_to_geojson(df)
  expect_equal(gj$type, "FeatureCollection")
  expect_length(gj$features, 2)
  expect_true(is_valid_geojson(gj))
  f2 <- gj$features[[2]]
  expect_equal(f2$geometry$type, "Point")
  expect_equal(f2$geometry$coordinates, c(72.8, 19.1))
  expect_equal(f2$properties$city, "Mumbai")
  expect_equal(f2$properties$pop, 2)
  expect_null(f2$properties$lon)

  empty <- convert_to_geojson(df[0, ])
  expect_length(empty$features, 0)
})

test_that("convert_to_geojson rejects non-tabular or coordinate-less input", {
  expect_error(convert_to_geojson(list(lon = 1, lat = 2)), "Cannot convert")
  expect_error(convert_to_geojson(data.frame(x = 1, y = 2)), "Cannot convert")
})

test_that("create_geojson_from_bbox output round-trips through sf", {
  gj <- create_geojson_from_bbox(north = 30, south = 20, east = 80, west = 70)
  f <- tempfile(fileext = ".geojson")
  on.exit(unlink(f), add = TRUE)
  jsonlite::write_json(gj, f, auto_unbox = TRUE)
  poly <- sf::st_read(f, quiet = TRUE)
  bb <- get_bbox_from_sf(poly)
  expect_equal(bb, c(xmin = 70, ymin = 20, xmax = 80, ymax = 30))
})

test_that("get_bbox_from_sf returns a plain named numeric vector", {
  pts <- sf::st_as_sf(data.frame(x = c(70, 75, 72), y = c(10, 15, 30)), coords = c("x", "y"), crs = 4326)
  bb <- get_bbox_from_sf(pts)
  expect_type(bb, "double")
  expect_named(bb, c("xmin", "ymin", "xmax", "ymax"))
  expect_equal(unname(bb), c(70, 10, 75, 30))
})

test_that("parse_date_flexible parses ISO dates", {
  expect_equal(parse_date_flexible("2023-01-05"), as.Date("2023-01-05"))
  expect_s3_class(parse_date_flexible("2024-02-29"), "Date")
  expect_equal(parse_date_flexible(as.Date("2023-02-01")), as.Date("2023-02-01"))
})

test_that("validate_bbox rejects degenerate boxes", {
  expect_false(validate_bbox(10, 10, 20, 10))
  expect_false(validate_bbox(10, 0, 10, 10))
  expect_false(validate_bbox(10, 0, 181, 10))
  expect_false(validate_bbox(NA, 0, 20, 10))
})

test_that("format_pressure_levels warns on levels the CDS does not offer", {
  expect_warning(out <- format_pressure_levels(c(1000, 999)), "Invalid pressure levels: 999")
  expect_equal(out, c("1000", "999"))
  expect_no_warning(format_pressure_levels(c(1000, 850, 500)))
})

test_that("format_date_range handles single days and leap years", {
  expect_equal(format_date_range(as.Date("2023-05-01"), as.Date("2023-05-01")), "2023-05-01")
  r <- format_date_range(as.Date("2024-02-27"), as.Date("2024-03-01"))
  expect_equal(r, c("2024-02-27", "2024-02-28", "2024-02-29", "2024-03-01"))
})

test_that("get_time_values falls back to hourly for unknown frequency", {
  expect_equal(get_time_values("weird"), sprintf("%02d:00", 0:23))
})

test_that("ensure_output_dir creates missing directories once", {
  d <- file.path(tempfile("varunayan_outdir_"), "nested", "dir")
  on.exit(unlink(dirname(dirname(d)), recursive = TRUE), add = TRUE)
  expect_message(res <- ensure_output_dir(d), "Created output directory")
  expect_true(dir.exists(d))
  expect_equal(res, d)
  expect_silent(ensure_output_dir(d))
})

test_that("cleanup_temp_files removes only matching files", {
  d <- tempfile("cleanup_")
  dir.create(d)
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  file.create(file.path(d, c("varunayan_a.nc", "varunayan_b.csv", "keep.txt")))
  expect_message(n <- cleanup_temp_files(directory = d), "Deleted 2 temporary files")
  expect_equal(n, 2)
  expect_equal(list.files(d), "keep.txt")
  expect_silent(n0 <- cleanup_temp_files(directory = d))
  expect_equal(n0, 0)
})

test_that("get_package_info reports versions and returns sessionInfo", {
  msgs <- capture_messages(info <- get_package_info())
  expect_s3_class(info, "sessionInfo")
  expect_true(any(grepl("^Platform: ", msgs)))
  expect_true(any(grepl("^sf: ", msgs)))
})

test_that("time_operation returns the value and records timing", {
  ns_env <- get(".varunayan_env", envir = asNamespace("varunayan"))
  old_timings <- ns_env$timings
  on.exit(ns_env$timings <- old_timings, add = TRUE)
  ns_env$timings <- list()
  msgs <- capture_messages(res <- time_operation(sum(1:10), "sum op"))
  expect_equal(res, 55)
  expect_true(any(grepl("\\[TIMER\\] Start: sum op", msgs)))
  expect_true(any(grepl("\\[TIMER\\] sum op: .* ms", msgs)))
  expect_silent(time_operation(1 + 1, "quiet", verbose = FALSE))
  expect_length(ns_env$timings, 2)
  expect_equal(ns_env$timings[[2]]$label, "quiet")
  expect_true(ns_env$timings[[1]]$elapsed >= 0)
})

test_that("get_timings formats durations across ms, seconds and minutes", {
  ns_env <- get(".varunayan_env", envir = asNamespace("varunayan"))
  old_timings <- ns_env$timings
  on.exit(ns_env$timings <- old_timings, add = TRUE)
  ns_env$timings <- list()
  expect_message(empty <- get_timings(), "There is no recorded time data")
  expect_equal(nrow(empty), 0)
  expect_named(empty, c("label", "elapsed_seconds", "timestamp"))

  now <- Sys.time()
  ns_env$timings <- list(
    list(label = "fast", elapsed = 0.25, timestamp = now),
    list(label = "medium", elapsed = 12.5, timestamp = now),
    list(label = "slow", elapsed = 125, timestamp = now)
  )
  df <- get_timings()
  expect_equal(df$label, c("fast", "medium", "slow"))
  expect_equal(df$duration, c("250.0 ms", "12.50 sec", "2m 5.0s"))
  expect_equal(df$elapsed_seconds, c(0.25, 12.5, 125))
})

test_that("print_timing_summary orders slowest first and reports shares", {
  ns_env <- get(".varunayan_env", envir = asNamespace("varunayan"))
  old_timings <- ns_env$timings
  on.exit(ns_env$timings <- old_timings, add = TRUE)
  ns_env$timings <- list()
  msgs <- capture_messages(res <- print_timing_summary())
  expect_true(any(grepl("No time data to show", msgs)))
  expect_null(res)

  now <- Sys.time()
  ns_env$timings <- list(
    list(label = "a", elapsed = 1, timestamp = now),
    list(label = "b", elapsed = 3, timestamp = now)
  )
  msgs <- capture_messages(df <- print_timing_summary())
  expect_equal(df$label, c("b", "a"))
  expect_true(any(grepl("Total operations: 2", msgs)))
  expect_true(any(grepl("1\\. b: 3.00 sec \\(75%\\)", msgs)))
  expect_true(any(grepl("2\\. a: 1.00 sec \\(25%\\)", msgs)))
})

test_that("clear_timings empties the timing store", {
  ns_env <- get(".varunayan_env", envir = asNamespace("varunayan"))
  old_timings <- ns_env$timings
  on.exit(ns_env$timings <- old_timings, add = TRUE)
  ns_env$timings <- list(list(label = "x", elapsed = 1, timestamp = Sys.time()))
  expect_message(clear_timings(), "The function cleared the time data")
  expect_length(ns_env$timings, 0)
})

test_that("read_cdsapirc parses key/url and ignores comments", {
  f <- tempfile()
  on.exit(unlink(f), add = TRUE)
  writeLines(c(
    "# comment line",
    "",
    "url: https://cds.climate.copernicus.eu/api",
    "  key:   abc-123:def  ",
    "garbage line without separator"
  ), f)
  creds <- read_cdsapirc(f)
  expect_equal(creds$url, "https://cds.climate.copernicus.eu/api")
  expect_equal(creds$key, "abc-123:def")
  expect_false("garbage line without separator" %in% names(creds))
})

test_that("read_cdsapirc returns NULL for missing file or missing key", {
  expect_null(read_cdsapirc(file.path(tempdir(), "definitely_missing_cdsapirc")))
  f <- tempfile()
  on.exit(unlink(f), add = TRUE)
  writeLines("url: https://example.invalid/api", f)
  expect_null(read_cdsapirc(f))
})

test_that("get_cds_credentials prefers the CDS_API_KEY environment variable", {
  old_key <- Sys.getenv("CDS_API_KEY", NA)
  on.exit(if (is.na(old_key)) Sys.unsetenv("CDS_API_KEY") else Sys.setenv(CDS_API_KEY = old_key), add = TRUE)
  Sys.setenv(CDS_API_KEY = "env-key-123")
  seen <- new.env()
  local_mocked_bindings(
    wf_set_key = function(key, ...) {
      seen$key <- key
      TRUE
    },
    wf_get_key = function(...) stop("keyring must not be consulted"),
    read_cdsapirc = function(...) stop("file must not be read")
  )
  msgs <- capture_messages(ok <- get_cds_credentials())
  expect_true(any(grepl("CDS_API_KEY", msgs)))
  expect_true(any(grepl("CDS credentials are configured", msgs)))
  expect_true(ok)
  expect_equal(seen$key, "env-key-123")
  expect_silent(get_cds_credentials(silent = TRUE))
})

test_that("get_cds_credentials falls back to the keyring", {
  old_key <- Sys.getenv("CDS_API_KEY", NA)
  on.exit(if (is.na(old_key)) Sys.unsetenv("CDS_API_KEY") else Sys.setenv(CDS_API_KEY = old_key), add = TRUE)
  Sys.unsetenv("CDS_API_KEY")
  local_mocked_bindings(
    wf_set_key = function(...) stop("should not set"),
    wf_get_key = function(...) "stored-key",
    read_cdsapirc = function(...) stop("file must not be read")
  )
  expect_message(ok <- get_cds_credentials(), "The package found the CDS credentials")
  expect_true(ok)
})

test_that("get_cds_credentials falls back to .cdsapirc", {
  old_key <- Sys.getenv("CDS_API_KEY", NA)
  on.exit(if (is.na(old_key)) Sys.unsetenv("CDS_API_KEY") else Sys.setenv(CDS_API_KEY = old_key), add = TRUE)
  Sys.unsetenv("CDS_API_KEY")
  seen <- new.env()
  local_mocked_bindings(
    wf_set_key = function(key, ...) {
      seen$key <- key
      TRUE
    },
    wf_get_key = function(...) stop("no key"),
    read_cdsapirc = function(...) list(url = "https://x.invalid", key = "file-key")
  )
  expect_true(suppressMessages(get_cds_credentials()))
  expect_equal(seen$key, "file-key")
})

test_that("get_cds_credentials returns FALSE when nothing is configured", {
  old_key <- Sys.getenv("CDS_API_KEY", NA)
  on.exit(if (is.na(old_key)) Sys.unsetenv("CDS_API_KEY") else Sys.setenv(CDS_API_KEY = old_key), add = TRUE)
  Sys.unsetenv("CDS_API_KEY")
  local_mocked_bindings(
    wf_set_key = function(...) stop("should not set"),
    wf_get_key = function(...) stop("no key"),
    read_cdsapirc = function(...) NULL
  )
  expect_warning(
    msgs <- capture_messages(ok <- get_cds_credentials()),
    "Cannot find CDS credentials"
  )
  expect_false(ok)
  expect_true(any(grepl("setup_cds_credentials", msgs)))
  expect_silent(ok2 <- get_cds_credentials(silent = TRUE))
  expect_false(ok2)
})

test_that("get_cds_credentials survives a failing wf_set_key", {
  old_key <- Sys.getenv("CDS_API_KEY", NA)
  on.exit(if (is.na(old_key)) Sys.unsetenv("CDS_API_KEY") else Sys.setenv(CDS_API_KEY = old_key), add = TRUE)
  Sys.setenv(CDS_API_KEY = "bad-key")
  local_mocked_bindings(
    wf_set_key = function(...) stop("keyring unavailable"),
    wf_get_key = function(...) "",
    read_cdsapirc = function(...) NULL
  )
  expect_false(get_cds_credentials(silent = TRUE))
})
