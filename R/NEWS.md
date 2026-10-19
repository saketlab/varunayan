# varunayan 0.4.0

* Initial CRAN submission.

* New analysis functions: 
  `load_india_boundaries()`, `spatial_mean()`, `compare()`,
  `cross_correlation()`, `anomaly()`, `seasonal_cycle()`, `peak_month()`,
  `seasonal_stat()`, `regrid()` and `dewpoint_from_relative_humidity()`.
* New ggplot2 plot functions: `plot_map()`, `plot_series()`,
  `plot_dual_axis()`, `plot_ccf()`, `plot_scatter()`, `plot_bars()` and
  `plot_heatmap()`.
* `era5ify_*()` with `frequency = "monthly"` or `"yearly"` return totals for
  accumulated variables such as precipitation (they returned the mean daily
  value), and always have `year` (and `month`) columns.
* `era5ify_point()` snaps its download box to the 0.25 degree grid, so the
  nearest cell is a true ERA5 grid point.
* `era5ify_*()` with `frequency = "yearly"` download the ERA5 monthly-means
  product, as in the Python package. Before, they downloaded one value at
  12:00 for each day.
* Shared test cases in `parity` check that R and Python give the same
  results.
