Command Line Interface Reference
================================

The varunayan command line interface provides three processing modes for different geographical input types.

Overview
--------

.. code-block:: bash

   varunayan <mode> [options]

Available modes:

- ``geojson``: Process using GeoJSON/JSON file
- ``bbox``: Process using bounding box coordinates  
- ``point``: Process using a single point (lat, lon)

Common Options
--------------

All modes support these common options:

Required Options
~~~~~~~~~~~~~~~~

``--request-id REQUEST_ID``
   Unique identifier for the request. Used for output directory and file naming.

``--variables VARIABLES``
   Comma-separated list of ERA5 variable names (e.g., "2m_temperature,total_precipitation").

``--start START_DATE``
   Start date in YYYY-MM-DD or YYYY-M-D format.

``--end END_DATE``
   End date in YYYY-MM-DD or YYYY-M-D format.

Optional Options
~~~~~~~~~~~~~~~~

``--dataset-type {single,pressure}``
   Type of ERA5 dataset. Default: "single"
   
   - ``single``: Single-level variables (surface and near-surface)
   - ``pressure``: Pressure-level variables (requires --pressure-levels)

``--pressure-levels LEVELS``
   Comma-separated pressure levels in hPa (e.g., "1000,925,850,500"). Required when dataset-type is "pressure".

``--freq {hourly,daily,weekly,monthly,yearly}``
   Temporal aggregation frequency. Default: "hourly"

``--res RESOLUTION``
   Grid resolution in degrees. Default: 0.25

``--verbosity {0,1,2}``
   Verbosity level: 0 (quiet), 1 (normal), 2 (verbose). Default: 0

``--save-raw {True,False}``
   Whether to save raw downloaded data. Default: True

GeoJSON Mode
------------

Process climate data for regions defined in GeoJSON files.

.. code-block:: bash

   varunayan geojson --request-id REQUEST_ID --variables VARIABLES \
                     --start START_DATE --end END_DATE \
                     --geojson GEOJSON_FILE [options]

Specific Options
~~~~~~~~~~~~~~~~

``--geojson GEOJSON_FILE``
   Path to GeoJSON or JSON file defining the region(s) of interest.

``--dist-features FEATURES``
   Comma-separated list of distinguishing feature names in the GeoJSON properties (e.g., "state,district").

Examples
~~~~~~~~

.. code-block:: bash

   # Basic usage with GeoJSON
   varunayan geojson --request-id "mumbai_weather" \
     --variables "2m_temperature,total_precipitation" \
     --start "2020-01-01" --end "2020-01-31" \
     --geojson "mumbai.geojson"

   # With distinguishing features
   varunayan geojson --request-id "indian_states" \
     --variables "2m_temperature" \
     --start "2020-06-01" --end "2020-08-31" \
     --geojson "india_states.geojson" \
     --dist-features "state_name,region" \
     --freq "monthly"

   # High-resolution pressure data
   varunayan geojson --request-id "cyclone_analysis" \
     --variables "u_component_of_wind,v_component_of_wind" \
     --start "2020-05-15" --end "2020-05-20" \
     --geojson "bay_of_bengal.geojson" \
     --dataset-type "pressure" \
     --pressure-levels "850,500,200" \
     --res 0.1 --freq "hourly"

Bounding Box Mode
-----------------

Process climate data for rectangular regions defined by coordinates.

.. code-block:: bash

   varunayan bbox --request-id REQUEST_ID --variables VARIABLES \
                  --start START_DATE --end END_DATE \
                  --north NORTH --south SOUTH --east EAST --west WEST [options]

Specific Options
~~~~~~~~~~~~~~~~

``--north LATITUDE``
   Northern boundary latitude in decimal degrees.

``--south LATITUDE``
   Southern boundary latitude in decimal degrees.

``--east LONGITUDE``
   Eastern boundary longitude in decimal degrees.

``--west LONGITUDE``
   Western boundary longitude in decimal degrees.

Examples
~~~~~~~~

.. code-block:: bash

   # California weather data
   varunayan bbox --request-id "california_2020" \
     --variables "2m_temperature,total_precipitation,10m_wind_speed" \
     --start "2020-01-01" --end "2020-12-31" \
     --north 42.0 --south 32.5 --east -114.1 --west -124.4 \
     --freq "daily"

   # High-resolution monsoon analysis
   varunayan bbox --request-id "monsoon_kerala" \
     --variables "total_precipitation,2m_temperature" \
     --start "2020-06-01" --end "2020-09-30" \
     --north 12.8 --south 8.2 --east 77.4 --west 74.9 \
     --res 0.1 --freq "daily"

   # Pressure level winds over Pacific
   varunayan bbox --request-id "pacific_winds" \
     --variables "u_component_of_wind,v_component_of_wind,temperature" \
     --start "2020-07-01" --end "2020-07-07" \
     --north 50.0 --south 10.0 --east -120.0 --west -180.0 \
     --dataset-type "pressure" \
     --pressure-levels "850,500,200"

Point Mode  
----------

Process climate data for specific point locations.

.. code-block:: bash

   varunayan point --request-id REQUEST_ID --variables VARIABLES \
                   --start START_DATE --end END_DATE \
                   --lat LATITUDE --lon LONGITUDE [options]

Specific Options
~~~~~~~~~~~~~~~~

``--lat LATITUDE``
   Latitude of the point in decimal degrees.

``--lon LONGITUDE``
   Longitude of the point in decimal degrees.

Examples
~~~~~~~~

.. code-block:: bash

   # Weather station data for New Delhi
   varunayan point --request-id "delhi_weather" \
     --variables "2m_temperature,total_precipitation,surface_pressure" \
     --start "2020-01-01" --end "2020-12-31" \
     --lat 28.6139 --lon 77.2090 \
     --freq "daily"

   # Hourly data for a specific location
   varunayan point --request-id "mumbai_hourly" \
     --variables "2m_temperature,2m_relative_humidity" \
     --start "2020-06-15" --end "2020-06-20" \
     --lat 19.0760 --lon 72.8777 \
     --freq "hourly"

   # Multi-level atmospheric profile
   varunayan point --request-id "sounding_data" \
     --variables "temperature,u_component_of_wind,v_component_of_wind" \
     --start "2020-01-01" --end "2020-01-01" \
     --lat 28.6 --lon 77.2 \
     --dataset-type "pressure" \
     --pressure-levels "1000,925,850,700,500,300,200,100"

Output Structure
----------------

All commands create an output directory named ``{request_id}_output/`` containing:

CSV Files
~~~~~~~~~

``{request_id}_{frequency}_data.csv``
   Main output file with aggregated climate data.

``{request_id}_unique_latlongs.csv`` 
   Unique coordinate pairs in the processed region.

``{request_id}_raw_data.csv``
   Raw downloaded data before aggregation (if --save-raw=True).

Common Variables
----------------

Single-Level Variables
~~~~~~~~~~~~~~~~~~~~~~

- ``2m_temperature``: Air temperature at 2 meters above surface
- ``total_precipitation``: Accumulated precipitation  
- ``10m_u_component_of_wind``: Eastward wind component at 10m
- ``10m_v_component_of_wind``: Northward wind component at 10m
- ``surface_pressure``: Pressure at surface
- ``mean_sea_level_pressure``: Sea level pressure
- ``2m_relative_humidity``: Relative humidity at 2m
- ``surface_solar_radiation_downwards``: Incoming solar radiation

Pressure-Level Variables  
~~~~~~~~~~~~~~~~~~~~~~~~

- ``temperature``: Air temperature at pressure levels
- ``u_component_of_wind``: Eastward wind component  
- ``v_component_of_wind``: Northward wind component
- ``geopotential``: Geopotential height
- ``relative_humidity``: Relative humidity
- ``specific_humidity``: Specific humidity

Error Handling
--------------

The CLI provides informative error messages for common issues:

Configuration Errors
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   Error: CDS API not configured. Please set up ~/.cdsapirc

Parameter Errors
~~~~~~~~~~~~~~~~

.. code-block:: bash

   Error: Start date must be before end date
   Error: Pressure levels required for pressure dataset type
   Error: GeoJSON file not found: region.geojson

Network Errors
~~~~~~~~~~~~~~

.. code-block:: bash

   Warning: Download failed, retrying...
   Error: Maximum retries exceeded for download

For detailed troubleshooting, increase verbosity with ``--verbosity 2``.