Release History
===============

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


