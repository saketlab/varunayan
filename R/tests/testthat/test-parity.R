# Run parity/cases.json; python/tests/test_parity.py runs the same cases.

cases_file <- testthat::test_path("..", "..", "..", "parity", "cases.json")
skip_if_not(file.exists(cases_file), "shared parity cases not found")
cases <- jsonlite::fromJSON(cases_file, simplifyVector = TRUE, simplifyDataFrame = FALSE)

na_from_null <- function(v) {
  if (is.list(v)) v <- vapply(v, function(e) if (is.null(e)) NA_real_ else as.numeric(e), numeric(1))
  if (is.logical(v)) v <- as.numeric(v)
  v
}

run_case <- function(case) {
  # era5_grid_output() is internal; every other function is exported.
  fn <- get(case$`function`, envir = asNamespace("varunayan"))
  args <- case$args
  # An empty JSON array means "no group columns".
  args <- lapply(args, function(a) if (is.list(a) && length(a) == 0) character(0) else a)
  if (!is.null(case$data)) {
    data <- as.data.frame(lapply(case$data, na_from_null), stringsAsFactors = FALSE)
    do.call(fn, c(list(data), args))
  } else {
    do.call(fn, args)
  }
}

for (case in cases) {
  test_that(paste("parity:", case$name), {
    got <- run_case(case)
    exp <- case$expected
    if (is.list(exp)) {
      expect_identical(names(got), names(exp))
      for (col in names(exp)) {
        if (col == "date") {
          expect_identical(format(got[[col]], "%Y-%m-%d"), unlist(exp[[col]]))
        } else if (col == "datetime") {
          expect_identical(format(got[[col]], "%Y-%m-%d %H:%M:%S", tz = "UTC"), unlist(exp[[col]]))
        } else if (is.character(exp[[col]])) {
          expect_identical(as.character(got[[col]]), exp[[col]])
        } else {
          expect_equal(as.numeric(got[[col]]), na_from_null(exp[[col]]),
            tolerance = case$tol, ignore_attr = TRUE, info = col
          )
        }
      }
    } else if (is.character(exp)) {
      expect_identical(as.character(got), exp)
    } else {
      expect_equal(as.numeric(got), na_from_null(exp), tolerance = case$tol)
    }
  })
}

test_that("parity cases cover every analysis function", {
  covered <- sort(unique(vapply(cases, function(c) c$`function`, character(1))))
  expect_identical(covered, sort(c(
    "spatial_mean", "compare", "cross_correlation", "anomaly", "seasonal_cycle",
    "peak_month", "seasonal_stat", "regrid", "dewpoint_from_relative_humidity",
    "era5_grid_output", "relative_humidity_from_dewpoint", "vapor_pressure_from_dewpoint",
    "wet_bulb_temperature", "wet_bulb_from_dewpoint", "heat_index", "heat_index_from_dewpoint",
    "humidex", "wbgt_simple", "wbgt_shade", "heat_index_risk_category", "wbgt_risk_category",
    "utci_category", "utci", "mean_radiant_temperature", "calc_heat_indices", "utci_sparse"
  )))
})

plot_cases <- jsonlite::fromJSON(sub("cases.json$", "plot_cases.json", cases_file),
  simplifyVector = TRUE, simplifyDataFrame = FALSE
)

for (case in plot_cases) {
  test_that(paste("parity plot:", case$name), {
    skip_if_not_installed("ggplot2")
    data <- as.data.frame(case$data, stringsAsFactors = FALSE)
    p <- do.call(getExportedValue("varunayan", case$`function`), c(list(data), case$args))
    expect_s3_class(p, "ggplot")
    built <- ggplot2::ggplot_build(p)
    expect_identical(length(unique(built$layout$layout$PANEL)), as.integer(case$expected$n_panels))
    labs <- ggplot2::get_labs(p)
    expect_identical(labs$title, case$expected$title)
    if (!is.null(case$expected$ylabel)) {
      ylab <- built$layout$panel_scales_y[[1]]$name
      if (is.null(ylab) || inherits(ylab, "waiver")) ylab <- labs$y
      expect_identical(ylab, case$expected$ylabel)
    }
  })
}
