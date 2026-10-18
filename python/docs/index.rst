varunayan: Climate Data Toolkit
================================

Download and process climate reanalysis and observational data from ERA5, IMD, HadEX3, and CRU TS. Compute heat stress indices (UTCI, WBGT, Heat Index, Humidex). Aggregate country-level temperature series. Built with a focus on India, but works globally wherever the underlying datasets have coverage.

.. image:: https://img.shields.io/pypi/v/varunayan.svg
   :target: https://pypi.org/project/varunayan/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/varunayan.svg
   :target: https://pypi.org/project/varunayan/
   :alt: Python versions

.. image:: https://img.shields.io/github/license/saketlab/varunayan.svg
   :target: https://github.com/saketlab/varunayan/blob/main/LICENSE
   :alt: License

.. note::

   **R users**: See `varunayanR <https://varunayanr.saketlab.org>`_, the R companion package.

Data Sources
------------

.. list-table::
   :header-rows: 1
   :widths: 20 50 30

   * - Source
     - Coverage
     - Access
   * - **ERA5**
     - Global reanalysis, 0.25° grid, 1940-present
     - CDS API (bbox, point, GeoJSON)
   * - **IMD**
     - India gridded rainfall (0.25°) and temperature (1°), 1901-present
     - Direct download
   * - **HadEX3**
     - Global ETCCDI climate extremes indices, 1.875° grid
     - Direct download
   * - **CRU TS**
     - Global monthly climate grids (0.5°), 1901-present
     - Direct download

Quick Start
-----------

.. code-block:: bash

   pip install varunayan

.. code-block:: python

   import varunayan

   # ERA5 temperature for a bounding box
   varunayan.era5ify_bbox(
       request_id="demo",
       variables=["2m_temperature"],
       start_date="2023-06-01",
       end_date="2023-06-30",
       north=28.7, south=28.5, east=77.3, west=77.0,
   )

   # IMD gridded rainfall
   varunayan.imd_rainfall_bbox(
       "mumbai", start_year=2020, end_year=2020,
       north=19.2, south=18.9, east=72.9, west=72.8,
   )

   # HadEX3 climate extremes
   varunayan.hadex3_bbox("TXx", start_year=2000, end_year=2018,
       north=35, south=8, east=90, west=68)

   # UTCI heat stress index
   varunayan.utci(temp_c=35.0, rh=60.0, wind_ms=2.0, mrt_c=50.0)

CLI
~~~

.. code-block:: bash

   varunayan bbox --request-id demo --variables 2m_temperature \
     --start 2023-06-01 --end 2023-06-30 \
     --north 28.7 --south 28.5 --east 77.3 --west 77.0

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   cli_reference
   examples
   contributing

Jupyter Notebooks
=================

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
