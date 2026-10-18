CLI Reference
=============

Command-line interface documentation.

Commands
--------

The ``varunayan`` command provides three subcommands:

geojson
^^^^^^^

Process climate data for regions defined by GeoJSON files.

.. code-block:: bash

    varunayan geojson [OPTIONS]

**Options:**

* ``--request-id TEXT`` - Unique identifier for the request [required]
* ``--variables TEXT`` - Comma-separated list of variables [required]
* ``--start-date TEXT`` - Start date (YYYY-MM-DD) [required]
* ``--end-date TEXT`` - End date (YYYY-MM-DD) [required]
* ``--json-file PATH`` - Path to GeoJSON file [required]
* ``--dataset-type [single|pressure]`` - Dataset type [default: single]
* ``--pressure-levels TEXT`` - Comma-separated pressure levels
* ``--frequency [hourly|daily|weekly|monthly|yearly]`` - Data frequency [default: hourly]
* ``--resolution FLOAT`` - Grid resolution in degrees [default: 0.25]

bbox
^^^^

Process climate data for rectangular regions.

.. code-block:: bash

    varunayan bbox [OPTIONS]

**Options:**

* ``--request-id TEXT`` - Unique identifier for the request [required]
* ``--variables TEXT`` - Comma-separated list of variables [required]
* ``--start-date TEXT`` - Start date (YYYY-MM-DD) [required]
* ``--end-date TEXT`` - End date (YYYY-MM-DD) [required]
* ``--north FLOAT`` - Northern boundary [required]
* ``--south FLOAT`` - Southern boundary [required]  
* ``--east FLOAT`` - Eastern boundary [required]
* ``--west FLOAT`` - Western boundary [required]
* ``--dataset-type [single|pressure]`` - Dataset type [default: single]
* ``--pressure-levels TEXT`` - Comma-separated pressure levels
* ``--frequency [hourly|daily|weekly|monthly|yearly]`` - Data frequency [default: hourly]
* ``--resolution FLOAT`` - Grid resolution in degrees [default: 0.25]

point
^^^^^

Process climate data for specific points.

.. code-block:: bash

    varunayan point [OPTIONS]

**Options:**

* ``--request-id TEXT`` - Unique identifier for the request [required]
* ``--variables TEXT`` - Comma-separated list of variables [required]
* ``--start-date TEXT`` - Start date (YYYY-MM-DD) [required]
* ``--end-date TEXT`` - End date (YYYY-MM-DD) [required]
* ``--latitude FLOAT`` - Latitude coordinate [required]
* ``--longitude FLOAT`` - Longitude coordinate [required]
* ``--dataset-type [single|pressure]`` - Dataset type [default: single]
* ``--pressure-levels TEXT`` - Comma-separated pressure levels
* ``--frequency [hourly|daily|weekly|monthly|yearly]`` - Data frequency [default: hourly]

Examples
--------

Download temperature and precipitation data for India:

.. code-block:: bash

    varunayan geojson \
        --request-id "india_weather" \
        --variables "2m_temperature,total_precipitation" \
        --start-date "2023-01-01" \
        --end-date "2023-01-31" \
        --json-file "india.geojson" \
        --frequency "daily"

Download pressure-level data for a bounding box:

.. code-block:: bash

    varunayan bbox \
        --request-id "pressure_data" \
        --variables "temperature,relative_humidity" \
        --start-date "2023-01-01" \
        --end-date "2023-01-31" \
        --north 30.0 --south 20.0 --east 80.0 --west 70.0 \
        --dataset-type "pressure" \
        --pressure-levels "1000,850,500" \
        --frequency "daily"