Release History
===============

Unreleased
----------

Breaking changes (the Python and R packages now give the same output):

* ``era5ify_bbox``, ``era5ify_geojson`` and ``era5ify_point`` return the grid
  in long format (``datetime, latitude, longitude, variable, value``), with
  temperatures in Celsius and precipitation in mm (``convert_units=True``).
  Monthly and yearly accumulated variables are totals. Use ``spatial_mean()``
  for a regional mean.
* ``era5ify_geojson(dist_features=...)`` is replaced by ``level="feature"``.
  The CLI option ``--dist-features`` is replaced by ``--level``.
* ``era5ify_point`` takes ``lat`` and ``lon`` and returns the nearest grid cell.
* ``save_raw`` is ``False`` by default.
* ``utci(temp_c, wind_speed, dewpoint_c, tmrt=None)`` and
  ``mean_radiant_temperature(temp_c, solar_radiation=None, wind_speed=None)``
  use the R arguments. ``calc_heat_indices(temp_c, dewpoint_c)`` returns a
  DataFrame.
* ``heat_index`` uses the NWS rule for the Rothfusz regression and ``humidex``
  uses the ECCC constant (1/273.15), as in R. WBGT and UTCI category labels
  are in sentence case.

New:

* Analysis functions: ``load_india_boundaries``, ``spatial_mean``,
  ``compare``, ``cross_correlation``, ``anomaly``, ``seasonal_cycle``,
  ``peak_month``, ``seasonal_stat``, ``regrid``,
  ``dewpoint_from_relative_humidity``.
* Plot functions: ``plot_map``, ``plot_series``, ``plot_dual_axis``,
  ``plot_ccf``, ``plot_scatter``, ``plot_bars``, ``plot_heatmap``.
* ``aggregate_to_polygons`` takes ``by`` and ``fill_empty``.
* Shared test cases in ``parity`` check that Python and R give the
  same results.

v0.3.0 (2026-06-27)
-------------------

* HadEX3 climate extremes (1901-2018) via ``hadex3_bbox``, ``hadex3_geojson``
* CRU TS v4.07 monthly grids (1901-2022) via ``cru_ts_bbox``, ``cru_ts_geojson``
* IMD gridded rainfall and temperature via ``imd_rainfall_bbox``, ``imd_temperature_bbox``, ``imd_rainfall_geojson``, ``imd_temperature_geojson``
* IMD station registry via ``get_imd_stations``
* Country-level ERA5 temperature via ``get_era5_country_temperature``
* Heat stress indices: UTCI, WBGT, Heat Index, Humidex, wet-bulb temperature, mean radiant temperature
* Risk category classifiers and ``calc_heat_indices`` convenience wrapper
* Spatial aggregation to administrative boundaries or custom polygons
* Download caching to skip redundant API calls
* Convenience helpers: ``daily_summary``, ``compute_wind_speed``, ``compute_heat_index``, ``compute_utci``
* Requires Python 3.10+ (dropped 3.9)
* Tests for heat stress, HadEX3, CRU TS, IMD, country aggregation
* Notebooks for heat stress, HadEX3, CRU TS, spatial aggregation, country temperature

v0.2.0 (2025-11-09)
-------------------

* Aggregation bug fixes
* Updated variable list

v0.1.1 (2025-10-15)
-------------------

* Fix cdsapi key input

v0.1.0 (2025-10-11)
-------------------

Initial release of varunayan.

Features
~~~~~~~~
- **Core functionality**: Download and process ERA5 climate data
- **Multiple input modes**: Support for GeoJSON files, bounding boxes, and point coordinates
- **Variable support**: All ERA5 single-level and pressure-level variables
- **Temporal aggregation**: Hourly, daily, weekly, monthly, and yearly frequencies
- **Spatial filtering**: Automatic filtering based on GeoJSON geometries
- **Command-line interface**: Full CLI with three processing modes
- **Python API**: Clean programmatic interface with era5ify_* functions

Data Processing
~~~~~~~~~~~~~~~
- Automatic sum variable adjustment for temporal aggregation
- CSV output with standardized column names
- Raw data preservation option


