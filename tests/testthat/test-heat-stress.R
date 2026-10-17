test_that("heat_index gives no NaN warning outside the dry-air adjustment range", {
  # 5 degC and 45 degC with dry air: the adjustment does not apply to these values
  expect_no_warning(hi <- heat_index(c(5, 45, 35), c(10, 10, 10)))
  expect_false(anyNA(hi))
})

test_that("heat_index applies the dry-air adjustment between 80 and 112 degF", {
  # 35 degC = 95 degF, RH 5%: adjustment = -((13 - 5) / 4) * sqrt(17 / 17) = -2 degF
  t_f <- 95
  rh <- 5
  hi_f <- -42.379 + 2.04901523 * t_f + 10.14333127 * rh - 0.22475541 * t_f * rh -
    0.00683783 * t_f^2 - 0.05481717 * rh^2 + 0.00122874 * t_f^2 * rh +
    0.00085282 * t_f * rh^2 - 0.00000199 * t_f^2 * rh^2 - 2
  expect_equal(heat_index(35, 5), (hi_f - 32) * 5 / 9)
})
