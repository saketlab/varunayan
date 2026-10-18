Quick Start Guide
=================

Basic Usage
-----------

Python API
~~~~~~~~~~~

First, import the necessary functions:

.. code-block:: python

   from varunayan import era5ify_geojson, era5ify_bbox, era5ify_point

GeoJSON Processing
~~~~~~~~~~~~~~~~~~

Process ERA5 data for a custom geographical region defined by a GeoJSON file:

.. code-block:: python

   # Download temperature and precipitation data for a region
   era5ify_geojson(
       request_id="mumbai_climate",
       variables=["2m_temperature", "total_precipitation"],
       start_date="2020-01-01",
       end_date="2020-01-31", 
       json_file="mumbai_region.geojson",
       frequency="daily"
   )

Bounding Box Processing
~~~~~~~~~~~~~~~~~~~~~~~

Process data for a rectangular region:

.. code-block:: python

   # Download data for Northern California
   era5ify_bbox(
       request_id="california_weather",
       variables=["2m_temperature", "10m_wind_speed"],
       start_date="2020-06-01",
       end_date="2020-06-30",
       north=42.0,
       south=36.0, 
       east=-120.0,
       west=-124.0,
       frequency="hourly"
   )

Point Processing
~~~~~~~~~~~~~~~~

Process data for a specific location:

.. code-block:: python

   # Download data for San Francisco
   era5ify_point(
       request_id="sf_weather",
       variables=["2m_temperature", "total_precipitation"],
       start_date="2020-01-01",
       end_date="2020-12-31",
       latitude=37.7749,
       longitude=-122.4194,
       frequency="monthly"
   )

Advanced Options
~~~~~~~~~~~~~~~~

Configure additional parameters:

.. code-block:: python

   # Download pressure level data
   era5ify_bbox(
       request_id="pressure_data",
       variables=["temperature", "u_component_of_wind"],
       start_date="2020-01-01",
       end_date="2020-01-02",
       north=40.0, south=35.0, east=-120.0, west=-125.0,
       dataset_type="pressure",
       pressure_levels=["500", "850", "1000"],
       frequency="hourly",
       resolution=0.1  # Higher resolution
   )

Command Line Interface
----------------------

Basic Commands
~~~~~~~~~~~~~~

.. code-block:: bash

   # Process with GeoJSON file
   varunayan geojson --request-id "my_request" \
     --variables "2m_temperature,total_precipitation" \
     --start "2020-01-01" --end "2020-01-31" \
     --geojson "region.geojson" --freq "daily"

   # Process with bounding box
   varunayan bbox --request-id "bbox_request" \
     --variables "2m_temperature,10m_wind_speed" \
     --start "2020-06-01" --end "2020-06-30" \
     --north 42.0 --south 36.0 --east -120.0 --west -124.0

   # Process for a point
   varunayan point --request-id "point_request" \
     --variables "2m_temperature" \
     --start "2020-01-01" --end "2020-01-02" \
     --lat 37.7749 --lon -122.4194

Advanced CLI Options
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Download pressure level data
   varunayan bbox --request-id "pressure_winds" \
     --variables "u_component_of_wind,v_component_of_wind" \
     --start "2020-01-01" --end "2020-01-02" \
     --north 40 --south 35 --east -120 --west -125 \
     --dataset-type "pressure" \
     --pressure-levels "500,850,1000" \
     --res 0.1

   # Specify distinguishing features for GeoJSON
   varunayan geojson --request-id "states_weather" \
     --variables "2m_temperature" \
     --start "2020-01-01" --end "2020-01-02" \
     --geojson "indian_states.geojson" \
     --dist-features "state_name"

Understanding Output
--------------------

Output Structure
~~~~~~~~~~~~~~~~

Each request creates a directory named ``{request_id}_output/`` containing:

- ``{request_id}_{frequency}_data.csv``: Aggregated climate data
- ``{request_id}_unique_latlongs.csv``: Unique coordinate pairs in the region  
- ``{request_id}_raw_data.csv``: Raw downloaded data (if save_raw=True)

Data Format
~~~~~~~~~~~

The main CSV file contains columns like:

- ``valid_time``: Timestamp of the data
- ``latitude``, ``longitude``: Spatial coordinates
- Variable columns (e.g., ``t2m`` for 2m temperature, ``tp`` for total precipitation)
- Optional: ``pressure_level`` for pressure level data
- Optional: Distinguishing feature columns from GeoJSON

Time Frequencies
~~~~~~~~~~~~~~~~

- ``hourly``: Original ERA5 temporal resolution
- ``daily``: Daily aggregates (mean for intensive variables, sum for extensive)
- ``weekly``: Weekly aggregates
- ``monthly``: Monthly aggregates with proper day-weighting
- ``yearly``: Yearly aggregates

Variable Names
~~~~~~~~~~~~~~

Common ERA5 variables:

- ``2m_temperature`` (t2m): Air temperature at 2 meters
- ``total_precipitation`` (tp): Accumulated precipitation  
- ``10m_u_component_of_wind`` (u10): Eastward wind at 10m
- ``10m_v_component_of_wind`` (v10): Northward wind at 10m
- ``surface_pressure`` (sp): Surface pressure
- ``mean_sea_level_pressure`` (msl): Sea level pressure

Error Handling
--------------

The library includes robust error handling for common issues:

.. code-block:: python

   from varunayan import era5ify_point
   
   try:
       era5ify_point(
           request_id="test",
           variables=["2m_temperature"],
           start_date="2020-01-01",
           end_date="2020-01-02", 
           latitude=37.7749,
           longitude=-122.4194
       )
   except FileNotFoundError as e:
       print(f"CDS API configuration error: {e}")
   except ValueError as e:
       print(f"Invalid parameters: {e}")
   except Exception as e:
       print(f"Download error: {e}")

Next Steps
----------

- Explore the :doc:`api_reference/index` for detailed API documentation
- Check out :doc:`examples` for more advanced usage patterns  
- See :doc:`cli_reference` for complete command line options
- Browse the Jupyter notebooks for interactive examples