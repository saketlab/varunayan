f_to_c <- function(f) (f - 32) * 5 / 9

# Inverse of the Magnus form in relative_humidity_from_dewpoint().
dewpoint_from_rh <- function(t, rh) {
  g <- log(rh / 100) + 17.625 * t / (243.04 + t)
  243.04 * g / (17.625 - g)
}
