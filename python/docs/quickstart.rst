Quick Start Guide
=================

Python API
----------

Import the download functions:

.. code-block:: python

   from varunayan import era5ify_geojson, era5ify_bbox, era5ify_point, spatial_mean

GeoJSON region
~~~~~~~~~~~~~~

Get ERA5 data for the grid cells inside a region from a GeoJSON file:

.. code-block:: python

   df = era5ify_geojson(
       request_id="mumbai_climate",
       variables=["2m_temperature", "total_precipitation"],
       start_date="2020-01-01",
       end_date="2020-01-31",
       json_file="mumbai_region.geojson",
       frequency="daily",
   )

To get one row for each feature (for example, each district), use
``level="feature"``. Each row has the mean of the cells inside the feature
and the feature properties:

.. code-block:: python

   districts = era5ify_geojson(
       request_id="district_temp",
       variables=["2m_temperature"],
       start_date="2020-01-01",
       end_date="2020-12-31",
       json_file="districts.geojson",
       frequency="monthly",
       level="feature",
   )

Bounding box
~~~~~~~~~~~~

.. code-block:: python

   df = era5ify_bbox(
       request_id="california_weather",
       variables=["2m_temperature", "10m_u_component_of_wind"],
       start_date="2020-06-01",
       end_date="2020-06-30",
       north=42.0, south=36.0, east=-120.0, west=-124.0,
       frequency="daily",
   )

Point
~~~~~

``era5ify_point`` returns the grid cell nearest to the point:

.. code-block:: python

   df = era5ify_point(
       request_id="sf_weather",
       variables=["2m_temperature", "total_precipitation"],
       start_date="2020-01-01",
       end_date="2020-12-31",
       lat=37.7749,
       lon=-122.4194,
       frequency="monthly",
   )

Pressure levels
~~~~~~~~~~~~~~~

.. code-block:: python

   df = era5ify_bbox(
       request_id="pressure_data",
       variables=["temperature", "u_component_of_wind"],
       start_date="2020-01-01",
       end_date="2020-01-02",
       north=40.0, south=35.0, east=-120.0, west=-125.0,
       dataset_type="pressure",
       pressure_levels=["500", "850", "1000"],
       frequency="hourly",
   )

Regional mean
~~~~~~~~~~~~~

The ``era5ify_*`` functions return each grid cell. Use ``spatial_mean`` to get
a regional mean, weighted by cos(latitude):

.. code-block:: python

   monthly = spatial_mean(df, "value", by=["variable", "year", "month"])

Command Line Interface
----------------------

.. code-block:: bash

   # GeoJSON region
   varunayan geojson --request-id "my_request" \
     --variables "2m_temperature,total_precipitation" \
     --start "2020-01-01" --end "2020-01-31" \
     --geojson "region.geojson" --freq "daily"

   # One row for each GeoJSON feature
   varunayan geojson --request-id "states_weather" \
     --variables "2m_temperature" \
     --start "2020-01-01" --end "2020-01-02" \
     --geojson "indian_states.geojson" --level feature

   # Bounding box
   varunayan bbox --request-id "bbox_request" \
     --variables "2m_temperature,10m_u_component_of_wind" \
     --start "2020-06-01" --end "2020-06-30" \
     --north 42.0 --south 36.0 --east -120.0 --west -124.0

   # Point
   varunayan point --request-id "point_request" \
     --variables "2m_temperature" \
     --start "2020-01-01" --end "2020-01-02" \
     --lat 37.7749 --lon -122.4194

See :doc:`cli_reference` for all options.

Output
------

Data format
~~~~~~~~~~~

The ``era5ify_*`` functions return a DataFrame in long format, the same as the
R package:

- ``datetime``: start of the time step
- ``latitude``, ``longitude``: grid cell
- ``pressure_level``: only for pressure-level data
- ``variable``: ERA5 short name, for example ``t2m`` or ``tp``
- ``value``: the value
- ``year`` and ``month`` for monthly data; ``year`` for yearly data

With ``level="feature"``, the feature properties replace ``latitude`` and
``longitude``.

Units
~~~~~

With ``convert_units=True`` (the default), temperatures are in °C and
precipitation is in mm. Set ``convert_units=False`` to keep the ERA5 units
(Kelvin and metres).

Time frequencies
~~~~~~~~~~~~~~~~

- ``hourly``: the ERA5 time steps
- ``daily``, ``weekly``: mean of intensive variables, sum of accumulated
  variables
- ``monthly``, ``yearly``: accumulated variables (for example precipitation)
  are totals for the period

Files
~~~~~

Each request writes these files to ``{request_id}_output/``:

- ``{request_id}_{frequency}_data.csv``: the long table
- ``{request_id}_unique_latlongs.csv``: the grid cells in the region
- ``{request_id}_raw_data.csv``: the downloaded grid, only with
  ``save_raw=True`` (the default is ``False``)

Common variables
~~~~~~~~~~~~~~~~

- ``2m_temperature`` (t2m): air temperature at 2 m
- ``total_precipitation`` (tp): accumulated precipitation
- ``10m_u_component_of_wind`` (u10): eastward wind at 10 m
- ``10m_v_component_of_wind`` (v10): northward wind at 10 m
- ``surface_pressure`` (sp): surface pressure
- ``mean_sea_level_pressure`` (msl): sea level pressure

Next Steps
----------

- :doc:`api_reference/index`: all functions
- :doc:`examples`: more examples
- :doc:`cli_reference`: all command line options
- The notebooks: worked analyses
