test_that("the cache key separates frequencies", {
  key <- function(frequency) {
    generate_cache_key(
      source = "era5", variables = "2m_temperature",
      start_date = "2020-01-01", end_date = "2020-01-02",
      dataset_type = "single", frequency = frequency
    )
  }
  expect_false(identical(key("daily"), key("hourly")))
})

test_that("a timed-out CDS request is an error, not a result", {
  expect_null(.cds_result_path(NULL))
  expect_identical(.cds_result_path("a.nc"), "a.nc")
  expect_error(.cds_result_path(list(status = "running")), "Timeout")
})

test_that("save_to_cache leaves no temporary file behind", {
  withr::local_options(varunayan.cache_dir = withr::local_tempdir())
  src <- tempfile(fileext = ".rds")
  saveRDS(1, src)
  cached <- suppressMessages(save_to_cache(src, "k"))
  expect_identical(readRDS(cached), 1)
  expect_length(list.files(dirname(cached), pattern = "\\.tmp$"), 0)
})
