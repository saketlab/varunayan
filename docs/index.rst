varunayan: Download and Process ERA5 Climate Data
==================================================

A Python package for end-to-end acquisition of processed ERA5 climate data with custom region support.

.. image:: https://img.shields.io/pypi/v/varunayan.svg
   :target: https://pypi.org/project/varunayan/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/varunayan.svg
   :target: https://pypi.org/project/varunayan/
   :alt: Python versions

.. image:: https://img.shields.io/github/license/saketlab/varunayan.svg
   :target: https://github.com/saketlab/varunayan/blob/main/LICENSE
   :alt: License

Overview
--------

varunayan provides a simple and powerful interface to download and process ERA5 climate data from the Copernicus Climate Data Store. It supports:

- **Custom geographical regions**: Use GeoJSON files, bounding boxes, or point coordinates
- **Multiple variables**: Download any ERA5 variable (temperature, precipitation, wind, etc.)
- **Flexible time periods**: From hourly to yearly data aggregations
- **Automatic processing**: Spatial filtering, temporal aggregation, and CSV output
- **Chunking support**: Efficient handling of large timeframes through automatic time-based chunking

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install varunayan

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from varunayan import era5ify_geojson, era5ify_bbox, era5ify_point

   # Download data for a GeoJSON region
   era5ify_geojson(
       request_id="geojson_request",
       variables=["2m_temperature", "total_precipitation"],
       start_date="2020-01-01",
       end_date="2020-01-31",
       json_file="my_region.geojson"
   )

   # Download data for a bounding box
   era5ify_bbox(
       request_id="bbox_request",
       variables=["2m_temperature", "total_precipitation"],
       start_date="2020-01-01",
       end_date="2020-01-02",
       north=20.0, south=15.0, east=70.0, west=85.0
   )

   # Download data for a single point
   era5ify_point(
       request_id="point_request",
       variables=["2m_temperature", "total_precipitation"],
       start_date="2020-01-01",
       end_date="2020-01-02",
       latitude=18.8995, longitude=72.8093
   )

Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Process with GeoJSON file
   varunayan geojson --request-id "geojson_request" --variables "2m_temperature,total_precipitation" \
     --start "2020-01-01" --end "2020-01-31" --geojson "region.geojson"

   # Process with bounding box
   varunayan bbox --request-id "bbox_request" --variables "2m_temperature,total_precipitation" \
     --start "2020-01-01" --end "2020-01-02" \
     --north 20.0 --south 15.0 --east 70.0 --west 85.0

   # Process for a single point
   varunayan point --request-id "point_request" --variables "2m_temperature,total_precipitation" \
     --start "2020-01-01" --end "2020-01-02" --lat 18.8995 --lon 72.8093

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   cli_reference
   examples
   contributing

Jupyter Notebooks
==================

Interactive notebooks with hands-on examples:

.. toctree::
   :maxdepth: 1

   notebooks/README
   notebooks/01_quickstart
   notebooks/02_era5_imd_comparison
   notebooks/03_temperature_change_india
   notebooks/04_umbrella_sales_India
   notebooks/05_sunscreen_sales_California
   notebooks/06_malaria_dengue_public_interest_trend
   notebooks/07_rainfall_peak_India
   notebooks/08_era5_imd_temp_comparison
   notebooks/09_pressure_level_data

API Reference
=============

.. toctree::
   :maxdepth: 2

   api_reference/index

Release History
===============

.. toctree::
   :maxdepth: 1

   history


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`