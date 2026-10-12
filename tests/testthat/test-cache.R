# Tests for R/cache.R. Every test redirects get_cache_dir() to a temp dir.

era5_touch <- function(dir, name, bytes = 1024L, mtime = NULL) {
  p <- file.path(dir, name)
  writeBin(as.raw(rep(1L, bytes)), p)
  if (!is.null(mtime)) Sys.setFileTime(p, mtime)
  p
}

test_that("get_cache_dir honours create and defaults to R_user_dir", {
  withr::local_options(varunayan.cache_dir = NULL)
  fake <- tempfile("userdir")
  local_mocked_bindings(R_user_dir = function(package, which) {
    expect_equal(package, "varunayan")
    expect_equal(which, "cache")
    fake
  })
  expect_equal(get_cache_dir(create = FALSE), fake)
  expect_false(dir.exists(fake))
  expect_equal(get_cache_dir(create = TRUE), fake)
  expect_true(dir.exists(fake))
  unlink(fake, recursive = TRUE)
})

test_that("get_cache_dir respects the varunayan.cache_dir option", {
  d <- tempfile("optcache")
  withr::local_options(varunayan.cache_dir = d)
  local_mocked_bindings(R_user_dir = function(...) stop("should not be called"))
  expect_equal(get_cache_dir(create = FALSE), d)
  expect_false(dir.exists(d))
  get_cache_dir()
  expect_true(dir.exists(d))
  unlink(d, recursive = TRUE)
})

test_that("generate_cache_key is deterministic and order-insensitive", {
  k1 <- generate_cache_key("ERA5", c("b", "a"), "2023-01-01", "2023-01-31",
    area = c(30, 70, 20, 80), resolution = 0.25, dataset_type = "single"
  )
  k2 <- generate_cache_key("era5", c("a", "b"), as.Date("2023-01-01"), "2023-01-31",
    area = c(30, 70, 20, 80), resolution = 0.25, dataset_type = "single"
  )
  expect_identical(k1, k2)
  expect_match(k1, "^era5_20230101_20230131_[0-9a-f]{32}$")

  # area rounding to 3 decimals
  k3 <- generate_cache_key("era5", c("a", "b"), "2023-01-01", "2023-01-31",
    area = c(30.0001, 70, 20, 80), resolution = 0.25, dataset_type = "single"
  )
  expect_identical(k1, k3)
})

test_that("generate_cache_key is sensitive to every parameter", {
  base <- list(
    source = "era5", variables = c("a", "b"), start_date = "2023-01-01",
    end_date = "2023-01-31", area = c(30, 70, 20, 80), resolution = 0.25,
    dataset_type = "pressure", var_type = "tmax", pressure_levels = c("500", "850")
  )
  k0 <- do.call(generate_cache_key, base)
  variants <- list(
    source = "imd", variables = c("a", "c"), start_date = "2023-01-02",
    end_date = "2023-02-01", area = c(31, 70, 20, 80), resolution = 0.5,
    dataset_type = "single", var_type = "tmin", pressure_levels = c("500", "700")
  )
  keys <- vapply(names(variants), function(p) {
    args <- base
    args[[p]] <- variants[[p]]
    do.call(generate_cache_key, args)
  }, character(1))
  expect_false(any(keys == k0))
  expect_equal(length(unique(keys)), length(keys))

  # Dropping an optional component changes the key too
  nores <- base
  nores$resolution <- NULL
  expect_false(identical(do.call(generate_cache_key, nores), k0))
  # pressure levels are sorted
  rev_pl <- base
  rev_pl$pressure_levels <- c("850", "500")
  expect_identical(do.call(generate_cache_key, rev_pl), k0)
})

test_that("check_cache returns NULL when cache dir is missing or empty", {
  d <- era5_local_cache()
  expect_null(check_cache("era5_x"))
  dir.create(d)
  expect_null(check_cache("era5_x"))
})

test_that("save_to_cache / check_cache round trip", {
  d <- era5_local_cache()
  src <- withr::local_tempfile(fileext = ".nc")
  writeLines("payload", src)
  key <- generate_cache_key("era5", "t2m", "2023-01-01", "2023-01-02")

  expect_message(cached <- save_to_cache(src, key), "Cached to:")
  expect_equal(cached, file.path(d, paste0(key, ".nc")))
  expect_equal(readLines(cached), "payload")
  expect_equal(check_cache(key), cached)
  expect_null(check_cache(generate_cache_key("era5", "t2m", "2023-01-01", "2023-01-03")))

  # .grd files also match
  src2 <- withr::local_tempfile(fileext = ".grd")
  writeLines("grd", src2)
  suppressMessages(save_to_cache(src2, "imd_key"))
  expect_equal(check_cache("imd_key"), file.path(d, "imd_key.grd"))
})

test_that("save_to_cache errors for a missing file", {
  era5_local_cache()
  expect_error(save_to_cache(file.path(tempdir(), "nope.nc"), "k"), "File does not exist")
})

test_that("list_cache handles missing dir, empty dir, and filtering", {
  d <- era5_local_cache()
  expect_message(res <- list_cache(), "Cache directory does not exist")
  expect_equal(nrow(res), 0)
  expect_named(res, c("file", "source", "size_mb", "modified"))

  dir.create(d)
  expect_message(res <- list_cache(), "No cached files found")
  expect_equal(nrow(res), 0)

  era5_touch(d, "era5_a.nc", bytes = 1024^2)
  era5_touch(d, "imd_b.grd", bytes = 1024^2 / 2)
  era5_touch(d, "other_c.nc")
  era5_touch(d, "ignored.txt")

  expect_message(res <- list_cache(), "Found 3 cached file\\(s\\)")
  expect_equal(nrow(res), 3)
  expect_equal(res$source[res$file == "era5_a.nc"], "era5")
  expect_equal(res$source[res$file == "imd_b.grd"], "imd")
  expect_equal(res$source[res$file == "other_c.nc"], "unknown")
  expect_equal(res$size_mb[res$file == "era5_a.nc"], 1)
  expect_equal(res$size_mb[res$file == "imd_b.grd"], 0.5)

  res_imd <- suppressMessages(list_cache(source = "IMD"))
  expect_equal(res_imd$file, "imd_b.grd")

  file.remove(file.path(d, "imd_b.grd"))
  expect_message(res <- list_cache(source = "imd"), "No imd files in cache")
  expect_equal(nrow(res), 0)
})

test_that("cache_stats reports counts and sizes", {
  d <- era5_local_cache()
  s <- cache_stats()
  expect_false(s$exists)
  expect_equal(s$n_files, 0)
  expect_equal(s$location, d)

  dir.create(d)
  s <- cache_stats()
  expect_true(s$exists)
  expect_equal(s$n_files, 0)

  era5_touch(d, "era5_1.nc", bytes = 1024^2, mtime = as.POSIXct("2020-01-01 00:00:00"))
  era5_touch(d, "era5_2.nc", bytes = 1024^2)
  era5_touch(d, "imd_1.grd", bytes = 1024^2)
  s <- cache_stats()
  expect_equal(s$n_files, 3)
  expect_equal(s$n_era5, 2)
  expect_equal(s$n_imd, 1)
  expect_equal(s$total_size_mb, 3)
  expect_equal(s$oldest_file, "2020-01-01 00:00:00")
})

test_that("show_cache_info prints a per-source summary", {
  d <- era5_local_cache()
  expect_message(res <- show_cache_info(), "does not exist yet")
  expect_null(res)

  dir.create(d)
  suppressMessages(expect_message(res <- show_cache_info(), "Cache is empty"))
  expect_null(res)

  era5_touch(d, "era5_1.nc", bytes = 1024^2)
  era5_touch(d, "imd_1.grd", bytes = 1024^2)
  msgs <- testthat::capture_messages(res <- show_cache_info())
  expect_true(any(grepl("Found 2 file", msgs)))
  expect_true(any(grepl("IMD: 1 files", msgs)))
  expect_true(any(grepl("ERA5: 1 files", msgs)))
  expect_named(res, c("name", "size_mb", "mtime"))
  expect_setequal(res$name, c("era5_1.nc", "imd_1.grd"))
})

test_that("clear_cache without confirmation filters by source and age", {
  d <- era5_local_cache()
  expect_message(expect_equal(clear_cache(confirm = FALSE), 0), "does not exist")
  dir.create(d)
  expect_message(expect_equal(clear_cache(confirm = FALSE), 0), "No cached files to delete")

  old <- Sys.time() - 10 * 86400
  era5_touch(d, "era5_old.nc", mtime = old)
  era5_touch(d, "era5_new.nc")
  era5_touch(d, "imd_old.grd", mtime = old)
  era5_touch(d, "imd_new.grd")

  expect_message(n <- clear_cache(source = "era5", older_than = 30, confirm = FALSE), "No files match")
  expect_equal(n, 0)

  expect_message(n <- clear_cache(source = "era5", older_than = 5, confirm = FALSE), "Deleted 1 file")
  expect_equal(n, 1)
  expect_setequal(list.files(d), c("era5_new.nc", "imd_old.grd", "imd_new.grd"))

  expect_message(n <- clear_cache(source = "imd", confirm = FALSE), "Deleted 2 file")
  expect_equal(n, 2)
  expect_equal(list.files(d), "era5_new.nc")

  expect_message(n <- clear_cache(confirm = FALSE), "Deleted 1 file")
  expect_equal(n, 1)
  expect_length(list.files(d), 0)
})

test_that("clear_cache with confirmation cancels on a non-'yes' answer", {
  # readline() returns "" immediately in non-interactive sessions
  skip_if(interactive())
  d <- era5_local_cache()
  dir.create(d)
  era5_touch(d, "era5_a.nc")

  testthat::capture_output(
    msgs <- testthat::capture_messages(n <- clear_cache(confirm = TRUE))
  )
  expect_equal(n, 0)
  expect_true(any(grepl("About to delete 1 file", msgs)))
  expect_true(any(grepl("Cancelled", msgs)))
  expect_true(file.exists(file.path(d, "era5_a.nc")))
})

test_that("populate_sample_cache warns when no sample directory exists", {
  era5_local_cache()
  withr::local_dir(withr::local_tempdir())
  expect_warning(res <- populate_sample_cache(), "Sample data directory not found")
  expect_null(res)
})

test_that("populate_sample_cache caches available samples once", {
  d <- era5_local_cache()
  wd <- withr::local_tempdir()
  dir.create(file.path(wd, "imd_samples"))
  writeLines("rain", file.path(wd, "imd_samples", "rain_2024.nc"))
  writeLines("tmax", file.path(wd, "imd_samples", "tmax_2024.grd"))
  withr::local_dir(wd)

  res <- suppressMessages(populate_sample_cache())
  expect_length(res, 2)
  expect_true(all(file.exists(unlist(res))))
  expect_true(all(startsWith(unlist(res), d)))

  msgs <- testthat::capture_messages(res2 <- populate_sample_cache())
  expect_true(any(grepl("already cached", msgs)))
  expect_equal(unname(unlist(res2)), unname(unlist(res)))

  res3 <- suppressMessages(populate_sample_cache(force = TRUE))
  expect_length(res3, 2)
})
