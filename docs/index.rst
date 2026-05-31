varunayan: Download and Process ERA5 Climate Data
==================================================

A Python package for downloading and processing ERA5 climate data with support for custom geographical regions:

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

.. note::

   **R users**: Check out `varunayanR <https://saketlab.github.io/varunayanR>`_, the R companion package for varunayan.

- **Custom geographical regions**: Use GeoJSON files, bounding boxes, or point coordinates
- **Multiple variables**: Download any ERA5 variable (temperature, precipitation, wind, etc.)
- **Flexible time periods**: From hourly to yearly data aggregation
- **Automatic processing**: Spatial filtering, temporal aggregation, and CSV output
- **Chunking support**: Handle large requests efficiently with automatic time-based chunking

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
       request_id="my_request",
       variables=["2m_temperature", "total_precipitation"],
       start_date="2020-01-01",
       end_date="2020-01-31",
       json_file="my_region.geojson"
   )

   # Download data for a bounding box
   era5ify_bbox(
       request_id="bbox_request", 
       variables=["2m_temperature"],
       start_date="2020-01-01",
       end_date="2020-01-02",
       north=40.0, south=35.0, east=-120.0, west=-125.0
   )

Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Process with GeoJSON file
   varunayan geojson --request-id "my_request" --variables "2m_temperature,total_precipitation" \
     --start "2020-01-01" --end "2020-01-31" --geojson "region.geojson"

   # Process with bounding box
   varunayan bbox --request-id "bbox_request" --variables "2m_temperature" \
     --start "2020-01-01" --end "2020-01-02" \
     --north 40.0 --south 35.0 --east -120.0 --west -125.0

   # Process for a single point
   varunayan point --request-id "point_request" --variables "2m_temperature" \
     --start "2020-01-01" --end "2020-01-02" --lat 37.7749 --lon -122.4194

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