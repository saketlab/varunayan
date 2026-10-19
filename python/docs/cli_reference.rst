Command Line Interface Reference
================================

The ``varunayan`` command has three modes, one for each type of region.

.. code-block:: bash

   varunayan <mode> [options]

- ``geojson``: a region from a GeoJSON or JSON file
- ``bbox``: a bounding box
- ``point``: the grid cell nearest to a point

Common options
--------------

Required:

``--request-id REQUEST_ID``
   Unique identifier for the request. It names the output directory and files.

``--variables VARIABLES``
   Comma-separated ERA5 variable names, for example
   ``"2m_temperature,total_precipitation"``.

``--start START``
   Start date, ``YYYY-MM-DD`` or ``YYYY-M-D``.

``--end END``
   End date, ``YYYY-MM-DD`` or ``YYYY-M-D``.

Optional:

``--dataset-type {single,pressure}``
   ``single`` for single-level variables, ``pressure`` for pressure-level
   variables. Default: ``single``.

``--pressure-levels LEVELS``
   Comma-separated pressure levels in hPa, for example ``"1000,925,850"``.
   Use with ``--dataset-type pressure``.

``--freq {hourly,daily,weekly,monthly,yearly}``
   Time step of the output. Default: ``hourly``.

``--res RES``
   Grid resolution in degrees. Default: ``0.25``. Point mode always uses
   0.25.

``--verbosity {0,1,2}``
   0 (quiet), 1 (normal) or 2 (verbose). Default: ``0``.

``--save-raw {True,False}``
   Also write the downloaded grid to ``{request_id}_raw_data.csv``. Default:
   ``False``, the same as the Python function.

GeoJSON mode
------------

.. code-block:: bash

   varunayan geojson --request-id ID --variables VARS --start START --end END \
                     --geojson FILE [--level {union,feature}] [options]

``--geojson GEOJSON``
   Path to a GeoJSON or JSON file.

``--level {union,feature}``
   ``union`` (default): one row for each grid cell inside the union of the
   features. ``feature``: one row for each feature (for example each state),
   with the mean of the cells inside it and the feature properties.

.. code-block:: bash

   # Grid cells inside a region
   varunayan geojson --request-id "mumbai_weather" \
     --variables "2m_temperature,total_precipitation" \
     --start "2020-01-01" --end "2020-01-31" \
     --geojson "mumbai.geojson"

   # One row for each state
   varunayan geojson --request-id "indian_states" \
     --variables "2m_temperature" \
     --start "2020-06-01" --end "2020-08-31" \
     --geojson "india_states.geojson" \
     --level feature --freq "monthly"

Bounding box mode
-----------------

.. code-block:: bash

   varunayan bbox --request-id ID --variables VARS --start START --end END \
                  --north N --south S --east E --west W [options]

``--north``, ``--south``
   Latitude bounds in decimal degrees.

``--east``, ``--west``
   Longitude bounds in decimal degrees.

.. code-block:: bash

   # Daily rainfall and temperature over Kerala
   varunayan bbox --request-id "monsoon_kerala" \
     --variables "total_precipitation,2m_temperature" \
     --start "2020-06-01" --end "2020-09-30" \
     --north 12.8 --south 8.2 --east 77.4 --west 74.9 \
     --freq "daily"

   # Pressure-level winds
   varunayan bbox --request-id "pacific_winds" \
     --variables "u_component_of_wind,v_component_of_wind,temperature" \
     --start "2020-07-01" --end "2020-07-07" \
     --north 50.0 --south 10.0 --east -120.0 --west -180.0 \
     --dataset-type "pressure" --pressure-levels "850,500,200"

Point mode
----------

.. code-block:: bash

   varunayan point --request-id ID --variables VARS --start START --end END \
                   --lat LAT --lon LON [options]

``--lat LAT``, ``--lon LON``
   Latitude and longitude of the point in decimal degrees. The output is the
   ERA5 grid cell nearest to the point.

.. code-block:: bash

   varunayan point --request-id "delhi_weather" \
     --variables "2m_temperature,total_precipitation" \
     --start "2020-01-01" --end "2020-12-31" \
     --lat 28.6139 --lon 77.2090 --freq "daily"

Output
------

Each command writes these files to ``{request_id}_output/``:

``{request_id}_{frequency}_data.csv``
   The data in long format: ``datetime``, ``latitude``, ``longitude``,
   ``pressure_level`` (pressure-level data only), ``variable`` and ``value``.
   Monthly data also has ``year`` and ``month``; yearly data has ``year``.
   Temperatures are in °C and precipitation is in mm.

``{request_id}_unique_latlongs.csv``
   The grid cells in the region.

``{request_id}_raw_data.csv``
   The downloaded grid before aggregation (only with ``--save-raw True``).

Errors
------

The CLI writes a log message when a date, region or variable is not valid,
and when a download fails after its retries. Use ``--verbosity 2`` to see
more detail.
