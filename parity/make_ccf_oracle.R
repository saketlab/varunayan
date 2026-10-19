# Write ccf_oracle.json from R stats::ccf; run from the repo root.
set.seed(20261018)
lead <- function(n, k) {
  # y follows x with a delay of k steps, so the peak is at lag -k.
  x <- cumsum(rnorm(n + k))
  list(x = x[(k + 1):(n + k)], y = x[1:n] + rnorm(n, sd = 0.3))
}
make <- function(name, x, y, max_lag) {
  cc <- stats::ccf(x, y, lag.max = max_lag, plot = FALSE)
  list(name = name, x = x, y = y, max_lag = max_lag,
       lag = as.integer(cc$lag), r = as.numeric(cc$acf))
}
seasonal <- sin(2 * pi * (1:120) / 12)
cases <- list(
  make("ccf_asymmetric_small", c(1, 3, 2, 5, 4, 6, 8, 7), c(2, 1, 4, 3, 6, 5, 7, 9), 3),
  make("ccf_white_noise", rnorm(50), rnorm(50), 10),
  with(lead(80, 2), make("ccf_x_leads_by_2", x, y, 6)),
  with(lead(60, 5), make("ccf_x_leads_by_5", x, y, 8)),
  make("ccf_seasonal_shift_1", seasonal, c(seasonal[-1], seasonal[1]), 12),
  make("ccf_seasonal_vs_noise", seasonal, seasonal + rnorm(120, sd = 0.5), 12),
  make("ccf_trend", seq_len(30) + rnorm(30), seq_len(30) * 2 + rnorm(30), 5),
  make("ccf_zero_lag_only", c(4, 2, 7, 1, 9), c(3, 1, 8, 2, 7), 0)
)
jsonlite::write_json(cases, "parity/ccf_oracle.json", auto_unbox = TRUE, digits = NA, pretty = TRUE)
cat("wrote", length(cases), "ccf cases\n")
