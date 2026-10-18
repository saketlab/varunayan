# Tests for ERA5 aggregation rules (R/variable_lists.R).

test_that("variable lists are character vectors of short/long name pairs", {
  for (v in list(sum_vars, max_vars, min_vars, rate_vars)) {
    expect_type(v, "character")
    expect_true(length(v) %% 2 == 0)
    expect_false(anyNA(v))
  }
  expect_true(all(c("tp", "total_precipitation", "ssrd") %in% sum_vars))
  expect_true(all(c("mx2t", "maximum_2m_temperature") %in% max_vars))
  expect_true(all(c("mn2t", "minimum_2m_temperature") %in% min_vars))
  expect_true(all(c("avg_tprate", "average_total_precipitation_rate") %in% rate_vars))
})

test_that("aggregation lists do not overlap", {
  expect_length(intersect(sum_vars, max_vars), 0)
  expect_length(intersect(sum_vars, min_vars), 0)
  expect_length(intersect(max_vars, min_vars), 0)
  expect_length(intersect(rate_vars, c(sum_vars, max_vars, min_vars)), 0)
})

test_that("exclude_cols covers coordinates and CDS metadata", {
  expect_true(all(c(
    "latitude", "longitude", "date", "time", "valid_time",
    "number", "expver", "datetime", "variable"
  ) %in% exclude_cols))
})

test_that("is_sum_var identifies accumulated variables", {
  expect_true(is_sum_var("tp"))
  expect_true(is_sum_var("total_precipitation"))
  expect_true(is_sum_var("TOTAL_PRECIPITATION"))
  expect_true(is_sum_var("ssrd"))
  expect_true(is_sum_var("evaporation"))
  # token match within an underscore-separated name
  expect_true(is_sum_var("tp_daily"))
  expect_false(is_sum_var("2m_temperature"))
  expect_false(is_sum_var("t2m"))
  expect_false(is_sum_var("maximum_2m_temperature"))
})

test_that("is_max_var / is_min_var identify extremes", {
  expect_true(is_max_var("mx2t"))
  expect_true(is_max_var("maximum_2m_temperature"))
  expect_true(is_max_var("Maximum_2m_Temperature"))
  expect_false(is_max_var("2m_temperature"))
  expect_false(is_max_var("mn2t"))

  expect_true(is_min_var("mn2t"))
  expect_true(is_min_var("minimum_2m_temperature"))
  expect_false(is_min_var("2m_temperature"))
  expect_false(is_min_var("mx2t"))
})

test_that("is_rate_var identifies rate variables", {
  expect_true(is_rate_var("avg_tprate"))
  expect_true(is_rate_var("average_total_precipitation_rate"))
  expect_true(is_rate_var("crr"))
  expect_false(is_rate_var("2m_temperature"))
  expect_false(is_rate_var("tp"))
})

test_that("categorize_variables splits variables by aggregation method", {
  vars <- c(
    "latitude", "longitude", "date", "number", "valid_time",
    "t2m", "tp", "ssrd", "mx2t", "mn2t", "avg_tprate", "u10"
  )
  out <- categorize_variables(vars)
  expect_named(out, c("sum", "max", "min", "rate", "avg"))
  expect_setequal(out$sum, c("tp", "ssrd"))
  expect_equal(out$max, "mx2t")
  expect_equal(out$min, "mn2t")
  expect_equal(out$rate, "avg_tprate")
  expect_setequal(out$avg, c("t2m", "u10"))

  # Every non-excluded variable lands in exactly one category here
  kept <- setdiff(vars, exclude_cols)
  expect_setequal(unlist(out, use.names = FALSE), kept)
  expect_false(any(exclude_cols %in% unlist(out)))
})

test_that("categorize_variables handles empty and all-excluded input", {
  out <- categorize_variables(character())
  expect_true(all(lengths(out) == 0))
  out2 <- categorize_variables(c("latitude", "longitude", "time"))
  expect_true(all(lengths(out2) == 0))
  out3 <- categorize_variables("2m_temperature")
  expect_equal(out3$avg, "2m_temperature")
})
