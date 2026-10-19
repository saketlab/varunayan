Examples
========

These examples show common tasks. All ``era5ify_*`` functions return a long
DataFrame with the columns ``datetime``, ``latitude``, ``longitude``,
``variable`` and ``value``. Temperatures are in °C and precipitation is in mm.

Monsoon rainfall for each state
-------------------------------

Use ``level="feature"`` to get one row for each GeoJSON feature.

.. code-block:: python

   from varunayan import era5ify_geojson

   states = era5ify_geojson(
       request_id="india_monsoon_2020",
       variables=["total_precipitation", "2m_temperature"],
       start_date="2020-06-01",
       end_date="2020-09-30",
       json_file="india_states.geojson",
       frequency="daily",
       level="feature",
   )
   rain = states[states["variable"] == "tp"]

The same request from the command line:

.. code-block:: bash

   varunayan geojson --request-id "india_monsoon_2020" \
     --variables "total_precipitation,2m_temperature" \
     --start "2020-06-01" --end "2020-09-30" \
     --geojson "india_states.geojson" \
     --level feature --freq "daily"

Regional monthly mean and anomaly
---------------------------------

.. code-block:: python

   from varunayan import anomaly, era5ify_bbox, plot_series, spatial_mean

   temp = era5ify_bbox(
       request_id="india_t2m",
       variables=["2m_temperature"],
       start_date="1991-01-01",
       end_date="2020-12-31",
       north=37.0, south=6.0, east=97.5, west=68.0,
       frequency="monthly",
   )
   monthly = spatial_mean(temp, "value", by=["year", "month"])
   monthly["anomaly"] = anomaly(monthly, "value", baseline=(1991, 2020))
   plot_series(monthly, x="date", y="anomaly", smooth="linear")

Seasonal cycle and peak month
-----------------------------

.. code-block:: python

   from varunayan import era5ify_bbox, peak_month, plot_map, seasonal_cycle

   rain = era5ify_bbox(
       request_id="kerala_rain",
       variables=["total_precipitation"],
       start_date="2001-01-01",
       end_date="2020-12-31",
       north=12.8, south=8.2, east=77.4, west=74.9,
       frequency="monthly",
   )
   cycle = seasonal_cycle(rain, "value")    # mean for each calendar month
   peak = peak_month(rain, "value")          # wettest month for each cell
   plot_map(peak, "peak_month", months=True)

Cyclone winds on pressure levels
--------------------------------

Pressure-level data has a ``pressure_level`` column.

.. code-block:: python

   from varunayan import era5ify_bbox

   winds = era5ify_bbox(
       request_id="amphan_cyclone",
       variables=["u_component_of_wind", "v_component_of_wind", "temperature"],
       start_date="2020-05-18",
       end_date="2020-05-21",
       north=25.0, south=15.0, east=95.0, west=85.0,
       dataset_type="pressure",
       pressure_levels=["1000", "925", "850", "700", "500"],
       frequency="hourly",
   )

City and rural points
---------------------

``era5ify_point`` returns the grid cell nearest to each point.

.. code-block:: python

   from varunayan import era5ify_point

   urban = era5ify_point(
       request_id="mumbai_urban",
       variables=["2m_temperature", "skin_temperature"],
       start_date="2020-03-01",
       end_date="2020-05-31",
       lat=19.076, lon=72.878,
       frequency="daily",
   )
   rural = era5ify_point(
       request_id="mumbai_rural",
       variables=["2m_temperature", "skin_temperature"],
       start_date="2020-03-01",
       end_date="2020-05-31",
       lat=19.5, lon=73.5,
       frequency="daily",
   )

Compare ERA5 with IMD
---------------------

.. code-block:: python

   from varunayan import compare, era5ify_bbox, imd_rainfall_bbox, spatial_mean

   box = dict(north=22.0, south=16.0, east=80.0, west=73.0)
   era5 = era5ify_bbox("mh_era5", ["total_precipitation"], "2015-01-01",
                       "2020-12-31", frequency="monthly", **box)
   imd = imd_rainfall_bbox("mh_imd", 2015, 2020, frequency="monthly", **box)

   era5_mean = spatial_mean(era5, "value", by=["year", "month"])

Merge ``era5_mean`` with the IMD regional mean on ``year`` and ``month``. Then
use ``compare(merged, "imd", "era5")`` to get ``n``, ``r``, ``bias`` and
``rmse``. See the ERA5 and IMD notebooks for the full steps.

Heat stress
-----------

.. code-block:: python

   from varunayan import calc_heat_indices, era5ify_point

   df = era5ify_point(
       request_id="delhi_heat",
       variables=["2m_temperature", "2m_dewpoint_temperature"],
       start_date="2024-05-01",
       end_date="2024-06-30",
       lat=28.6, lon=77.2,
       frequency="daily",
   )
   wide = df.pivot_table(index="datetime", columns="variable", values="value")
   indices = calc_heat_indices(wide["t2m"], wide["d2m"])

Large requests
--------------

varunayan splits long requests into smaller CDS requests (up to 100 months for
monthly data, up to 14 days for hourly and daily data):

.. code-block:: python

   era5ify_bbox(
       request_id="large_dataset",
       variables=["2m_temperature"],
       start_date="2000-01-01",
       end_date="2020-12-31",
       north=50.0, south=0.0, east=100.0, west=50.0,
       frequency="daily",
   )

Send single-level and pressure-level variables in separate requests.
