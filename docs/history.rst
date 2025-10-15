Release History
===============

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


