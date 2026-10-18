Examples
========

This section provides comprehensive examples of using varunayan for various climate data analysis tasks.

Monsoon Analysis
----------------

Download and analyze monsoon precipitation patterns over India.

Python API
~~~~~~~~~~

.. code-block:: python

   from varunayan import era5ify_geojson

   # Download monsoon precipitation data
   era5ify_geojson(
       request_id="india_monsoon_2020",
       variables=["total_precipitation", "2m_temperature"],
       start_date="2020-06-01", 
       end_date="2020-09-30",
       json_file="india_states.geojson",
       dist_features=["state_name"],
       frequency="daily"
   )

Command Line
~~~~~~~~~~~~

.. code-block:: bash

   varunayan geojson --request-id "india_monsoon_2020" \
     --variables "total_precipitation,2m_temperature" \
     --start "2020-06-01" --end "2020-09-30" \
     --geojson "india_states.geojson" \
     --dist-features "state_name" \
     --freq "daily"

Hurricane/Cyclone Analysis
--------------------------

Analyze atmospheric conditions during extreme weather events.

Pressure Level Winds
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from varunayan import era5ify_bbox

   # Download multi-level wind data during Cyclone Amphan
   era5ify_bbox(
       request_id="amphan_cyclone",
       variables=["u_component_of_wind", "v_component_of_wind", "temperature"],
       start_date="2020-05-18",
       end_date="2020-05-21", 
       north=25.0, south=15.0, east=95.0, west=85.0,
       dataset_type="pressure",
       pressure_levels=["1000", "925", "850", "700", "500"],
       frequency="hourly",
       resolution=0.1
   )

Surface Conditions
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Surface pressure and wind patterns
   varunayan bbox --request-id "amphan_surface" \
     --variables "mean_sea_level_pressure,10m_u_component_of_wind,10m_v_component_of_wind" \
     --start "2020-05-18" --end "2020-05-21" \
     --north 25.0 --south 15.0 --east 95.0 --west 85.0 \
     --freq "hourly" --res 0.1

Urban Heat Island Study
-----------------------

Compare temperatures between urban and rural areas.

City vs Surroundings
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from varunayan import era5ify_point

   # Urban center (Mumbai)
   era5ify_point(
       request_id="mumbai_urban",
       variables=["2m_temperature", "surface_temperature"],
       start_date="2020-03-01",
       end_date="2020-05-31",
       latitude=19.0760,
       longitude=72.8777,
       frequency="hourly"
   )

   # Rural area nearby
   era5ify_point(
       request_id="mumbai_rural", 
       variables=["2m_temperature", "surface_temperature"],
       start_date="2020-03-01",
       end_date="2020-05-31",
       latitude=19.2,
       longitude=73.2,
       frequency="hourly"
   )

Agricultural Applications
-------------------------

Climate data for crop monitoring and yield prediction.

Growing Season Analysis
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from varunayan import era5ify_geojson

   # Download data for agricultural regions
   era5ify_geojson(
       request_id="punjab_agriculture",
       variables=[
           "2m_temperature", "total_precipitation", 
           "2m_relative_humidity", "surface_solar_radiation_downwards"
       ],
       start_date="2020-04-01",  # Kharif season start
       end_date="2020-10-31",   # Kharif season end
       json_file="punjab_districts.geojson",
       dist_features=["district_name"],
       frequency="daily"
   )

Frost Risk Assessment
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Daily minimum temperatures for winter wheat
   varunayan geojson --request-id "wheat_frost_risk" \
     --variables "2m_temperature,2m_dewpoint_temperature" \
     --start "2019-12-01" --end "2020-03-31" \
     --geojson "wheat_growing_regions.geojson" \
     --dist-features "region_name" \
     --freq "daily"

Renewable Energy Assessment
---------------------------

Solar and wind resource evaluation.

Solar Resource Mapping
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from varunayan import era5ify_bbox

   # Solar radiation data for Rajasthan (major solar potential)
   era5ify_bbox(
       request_id="rajasthan_solar", 
       variables=[
           "surface_solar_radiation_downwards",
           "surface_net_solar_radiation",
           "total_cloud_cover"
       ],
       start_date="2019-01-01",
       end_date="2021-12-31",
       north=30.2, south=23.0, east=78.3, west=69.3,
       frequency="monthly"
   )

Wind Energy Assessment
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Wind speeds at multiple heights for wind farm planning
   varunayan bbox --request-id "gujarat_wind" \
     --variables "10m_u_component_of_wind,10m_v_component_of_wind,100m_u_component_of_wind,100m_v_component_of_wind" \
     --start "2020-01-01" --end "2020-12-31" \
     --north 24.7 --south 20.1 --east 74.5 --west 68.1 \
     --freq "daily"

Climate Change Studies
----------------------

Long-term temperature and precipitation trends.

Temperature Trends
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from varunayan import era5ify_geojson

   # Multi-decade temperature analysis
   for year in range(1990, 2021, 5):
       era5ify_geojson(
           request_id=f"india_temp_{year}_{year+4}",
           variables=["2m_temperature"],
           start_date=f"{year}-01-01",
           end_date=f"{year+4}-12-31", 
           json_file="india_climate_zones.geojson",
           dist_features=["climate_zone"],
           frequency="yearly"
       )

Extreme Events
~~~~~~~~~~~~~~

.. code-block:: bash

   # Heat wave analysis
   varunayan bbox --request-id "delhi_heatwave_2019" \
     --variables "2m_temperature,maximum_2m_temperature_since_previous_post_processing" \
     --start "2019-05-01" --end "2019-06-30" \
     --north 29.0 --south 28.0 --east 77.5 --west 76.5 \
     --freq "daily"

Hydrology and Water Resources
-----------------------------

Precipitation and evaporation analysis for water management.

Catchment Analysis
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from varunayan import era5ify_geojson

   # Water balance components for river basin
   era5ify_geojson(
       request_id="ganga_basin_hydro",
       variables=[
           "total_precipitation", "total_evaporation",
           "runoff", "soil_temperature_level_1"
       ],
       start_date="2020-01-01",
       end_date="2020-12-31",
       json_file="ganga_basin.geojson",
       frequency="monthly"
   )

Drought Monitoring
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Precipitation deficit analysis
   varunayan geojson --request-id "maharashtra_drought_2019" \
     --variables "total_precipitation,soil_water_content,2m_temperature" \
     --start "2019-01-01" --end "2019-12-31" \
     --geojson "maharashtra_districts.geojson" \
     --dist-features "district_name" \
     --freq "monthly"

Aviation and Transport
----------------------

Weather data for aviation route planning and safety.

Upper Air Analysis
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from varunayan import era5ify_bbox

   # Flight level weather conditions
   era5ify_bbox(
       request_id="flight_route_weather",
       variables=[
           "temperature", "u_component_of_wind", "v_component_of_wind",
           "relative_humidity"
       ],
       start_date="2020-12-01",
       end_date="2020-12-31",
       north=35.0, south=8.0, east=95.0, west=65.0,  # India flight routes
       dataset_type="pressure", 
       pressure_levels=["300", "250", "200"],  # Flight levels
       frequency="hourly"
   )

Turbulence Analysis
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Wind shear and turbulence indicators
   varunayan point --request-id "delhi_airport_winds" \
     --variables "u_component_of_wind,v_component_of_wind,temperature" \
     --start "2020-01-01" --end "2020-01-31" \
     --lat 28.5562 --lon 77.1000 \
     --dataset-type "pressure" \
     --pressure-levels "1000,925,850,700,500,300,250,200" \
     --freq "hourly"

High-Resolution Local Studies
-----------------------------

Detailed analysis for small geographical areas.

Microclimate Analysis
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from varunayan import era5ify_bbox

   # High-resolution urban microclimate
   era5ify_bbox(
       request_id="bangalore_microclimate",
       variables=[
           "2m_temperature", "10m_wind_speed", "2m_relative_humidity",
           "surface_solar_radiation_downwards"
       ],
       start_date="2020-06-01",
       end_date="2020-06-30",
       north=13.1, south=12.8, east=77.8, west=77.4,  # Bangalore city
       resolution=0.1,  # High resolution
       frequency="hourly"
   )

Coastal Weather
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Coastal wind patterns for marine applications  
   varunayan bbox --request-id "mumbai_coastal" \
     --variables "10m_u_component_of_wind,10m_v_component_of_wind,mean_sea_level_pressure,significant_height_of_combined_wind_waves_and_swell" \
     --start "2020-06-01" --end "2020-09-30" \
     --north 19.3 --south 18.9 --east 72.9 --west 72.7 \
     --res 0.1 --freq "hourly"

Data Processing Tips
--------------------

Handling Large Datasets
~~~~~~~~~~~~~~~~~~~~~~~~

For large temporal or spatial extents, varunayan automatically chunks requests:

.. code-block:: python

   # This will be automatically chunked into smaller requests
   era5ify_bbox(
       request_id="large_dataset",
       variables=["2m_temperature"],
       start_date="2000-01-01",  # 20+ years of data
       end_date="2020-12-31",
       north=50.0, south=0.0, east=100.0, west=50.0,
       frequency="daily"
   )

Multiple Variables
~~~~~~~~~~~~~~~~~~

Download different variable types in separate requests for efficiency:

.. code-block:: bash

   # Surface variables
   varunayan bbox --request-id "surface_vars" \
     --variables "2m_temperature,total_precipitation,10m_wind_speed" \
     --start "2020-01-01" --end "2020-12-31" \
     --north 30 --south 20 --east 80 --west 70

   # Pressure level variables (separate request)
   varunayan bbox --request-id "pressure_vars" \
     --variables "temperature,u_component_of_wind,v_component_of_wind" \
     --start "2020-01-01" --end "2020-12-31" \
     --north 30 --south 20 --east 80 --west 70 \
     --dataset-type "pressure" --pressure-levels "850,500,200"