```python
import varunayan
```


```python
# varunayan.era5ify_geojson(request_id, variables, start_date, end_date, json_file, dataset_type, pressure_levels, frequency, resolution)
# request_id : str, unique identifier for the request
# variables : list, list of variables to download
# start_date : string, start date of the data ('YYYY-M-D' or 'YYYY-MM-DD')
# end_date : string, end date of the data ('YYYY-M-D' or 'YYYY-MM-DD')
# json_file : str, path to the geojson file containing the area of interest
# dataset_type : str, type of dataset (single or pressure, for single level or pressure level datasets), optional (single by default)
# pressure_levels : list, list of strings of pressure levels to download (e.g., ["1000", "925", "850"]), optional (empty by default)
# frequency : str, frequency of the data (hourly, daily, weekly, monthly, yearly), optional (hourly by default)
# resolution : float, resolution of the data in degrees (0.1, 0.25, etc.), optional (0.25 by default)
```


```python
df = varunayan.era5ify_geojson(
    request_id="test",
    variables=[
        "2m_temperature",
        "total_precipitation",
        "surface_pressure",
        "2m_dewpoint_temperature",
    ],
    start_date="2023-1-1",
    end_date="2023-1-28", 
    json_file="../data/india.json",
    dataset_type="single",
    frequency="daily",
    resolution="0.25",
)
```

    [0m✓ CDS API configuration is already set up and valid.[0m
    [0m
    ============================================================[0m
    [0m[0;34mSTARTING ERA5 SINGLE LEVEL PROCESSING[0m[0m
    [0m============================================================[0m
    [0mRequest ID: test[0m
    [0mVariables: ['2m_temperature', 'total_precipitation', 'surface_pressure', '2m_dewpoint_temperature'][0m
    [0mDate Range: 2023-01-01 to 2023-01-28[0m
    [0mFrequency: daily[0m
    [0mResolution: 0.25°[0m
    [0mGeoJSON File: C:\Users\ATHARV~1\AppData\Local\Temp\test_temp_geojson.json[0m
    [0m[0;32m✓ All inputs validated successfully[0m[0m
    [0m
    --- Bounding Box ---[0m
    [0m[0;32m✓ Bounding Box calculated:[0m[0m
    [0m  North: 35.4940°[0m
    [0m  South: 7.9655°[0m
    [0m  East:  97.4026°[0m
    [0m  West:  68.1766°[0m
    [0m  Area:  29.2259° × 27.5285°[0m
    
    
    --- GeoJSON Mini Map ---
    
    [0;34mMINI MAP (68.18°W to 97.40°E, 7.97°S to 35.49°N):[0m
    ┌─────────────────────────────────────────┐
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    └─────────────────────────────────────────┘
     [0;32m■[0m = Inside the shape
     [0;31m·[0m = Outside the shape
    [0m
    --- Processing Strategy ---[0m
    [0mUsing monthly dataset: False[0m
    [0mTotal days to process: 28[0m
    [0mMax days per chunk: 14[0m
    [0mNeeds chunking: True[0m
    [0m[0;36mPROCESSING CHUNK 1/2[0m
    Date Range: 2023-01-01 to 2023-01-14
    Variables:  2m_temperature, total_precipitation, surface_pressure, 2m_dewpoint_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 14:51:28,371 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 14:51:29,292 INFO Request ID is 2ac4d14c-c286-49d2-93d3-58499c9cffa8
    INFO:datapi.legacy_api_client:Request ID is 2ac4d14c-c286-49d2-93d3-58499c9cffa8
    2025-07-15 14:51:29,498 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 14:52:03,087 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 14:52:20,392 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                              

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\test_chunk1.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\test_chunk1.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test_chunk1\data_stream-oper_stepType-accum.nc[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test_chunk1\data_stream-oper_stepType-instant.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 2 file(s)[0m
    [0m  Processing file 1/2: data_stream-oper_stepType-accum.nc[0m


    

    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 336, 'latitude': 111, 'longitude': 117})[0m
    [0m  Processing file 2/2: data_stream-oper_stepType-instant.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 336, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.59 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 4363632 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 4363632 to 1493856 rows[0m
    [0m✓ Dataset filtering completed in 3.18 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 3.78 seconds[0m
    [0mFinal DataFrame shape: (1493856, 9)[0m
    [0mRows in final dataset: 1493856[0m
    [0m[0;32m✓ Chunk completed in 82.4 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 2/2[0m
    Date Range: 2023-01-15 to 2023-01-28
    Variables:  2m_temperature, total_precipitation, surface_pressure, 2m_dewpoint_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 14:53:02,070 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 14:53:02,888 INFO Request ID is 54a7a8dc-77b7-4e07-9f4a-c787761ae8cf
    INFO:datapi.legacy_api_client:Request ID is 54a7a8dc-77b7-4e07-9f4a-c787761ae8cf
    2025-07-15 14:53:03,092 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 14:53:12,105 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                              

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\test_chunk2.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\test_chunk2.zip[0m
    [0mExtracted NetCDF files:[0m


    

    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test_chunk2\data_stream-oper_stepType-accum.nc[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test_chunk2\data_stream-oper_stepType-instant.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 2 file(s)[0m
    [0m  Processing file 1/2: data_stream-oper_stepType-accum.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 336, 'latitude': 111, 'longitude': 117})[0m
    [0m  Processing file 2/2: data_stream-oper_stepType-instant.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 336, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.54 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 4363632 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 4363632 to 1493856 rows[0m
    [0m✓ Dataset filtering completed in 3.05 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 3.60 seconds[0m
    [0mFinal DataFrame shape: (1493856, 9)[0m
    [0mRows in final dataset: 1493856[0m
    [0m[0;32m✓ Chunk completed in 65.5 seconds[0m[0m
    [0m[0;34mAGGREGATING DATA (DAILY)[0m[0m
    [0mAggregating data to daily frequency...[0m
    [0mSum columns: ['tp'][0m
    [0mMax columns: [][0m
    [0mMin columns: [][0m
    [0mRate columns: [][0m
    [0mAverage columns: ['t2m', 'sp', 'd2m'][0m
    [0mAggregation completed in:   0.62 seconds[0m
    [0m
    Saving files to output directory: test_output[0m
    [0m  Saved final data to: test_output\test_daily_data.csv[0m
    [0m  Saved unique coordinates to: test_output\test_unique_latlongs.csv[0m
    [0m  Saved raw data to: test_output\test_raw_data.csv[0m
    [0m
    ============================================================[0m
    [0m[0;32mPROCESSING COMPLETE[0m[0m
    [0m============================================================[0m
    [0m
    [0;36mRESULTS SUMMARY:[0m[0m
    [0m----------------------------------------[0m
    [0mVariables processed: 4[0m
    [0mTime period:         2023-01-01 to 2023-01-28[0m
    [0mFinal output shape:  (28, 8)[0m
    [0mTotal complete processing time: 175.49 seconds[0m
    [0m
    First 5 rows of aggregated data:[0m
    [0m         tp         t2m            sp         d2m  year  month  day  \
    0  0.000155  289.156586  95582.187500  283.245087  2023      1    1   
    1  0.000184  288.782196  95621.062500  283.129059  2023      1    2   
    2  0.000141  288.308716  95639.898438  282.865387  2023      1    3   
    3  0.000200  287.533905  95647.882812  281.997925  2023      1    4   
    4  0.000143  287.359467  95756.250000  281.820160  2023      1    5   
    
             date  
    0  2023-01-01  
    1  2023-01-02  
    2  2023-01-03  
    3  2023-01-04  
    4  2023-01-05  [0m
    [0m
    ============================================================[0m
    [0m[0;34mERA5 SINGLE LEVEL PROCESSING COMPLETED SUCCESSFULLY[0m[0m
    [0m============================================================[0m



```python
df = varunayan.era5ify_geojson(
    request_id="test2",
    variables=[
        "2m_temperature", 
        "total_precipitation"
    ],
    start_date="2024-1-1",
    end_date="2024-12-31",
    json_file="../data/latvia.geojson",
    dataset_type="single",
    frequency="monthly",
    resolution="0.1",
)
```

    [0m✓ CDS API configuration is already set up and valid.[0m
    [0m
    ============================================================[0m
    [0m[0;34mSTARTING ERA5 SINGLE LEVEL PROCESSING[0m[0m
    [0m============================================================[0m
    [0mRequest ID: test2[0m
    [0mVariables: ['2m_temperature', 'total_precipitation'][0m
    [0mDate Range: 2024-01-01 to 2024-12-31[0m
    [0mFrequency: monthly[0m
    [0mResolution: 0.1°[0m
    [0mGeoJSON File: C:\Users\ATHARV~1\AppData\Local\Temp\test2_temp_geojson.json[0m
    [0m[0;32m✓ All inputs validated successfully[0m[0m
    [0m
    --- Bounding Box ---[0m
    [0m[0;32m✓ Bounding Box calculated:[0m[0m
    [0m  North: 58.0856°[0m
    [0m  South: 55.6776°[0m
    [0m  East:  28.2431°[0m
    [0m  West:  20.9537°[0m
    [0m  Area:  7.2894° × 2.4080°[0m
    
    
    --- GeoJSON Mini Map ---
    
    [0;34mMINI MAP (20.95°W to 28.24°E, 55.68°S to 58.09°N):[0m
    ┌────────────────────────────────────────────────────────────┐
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m│
    │[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;31m·[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    └────────────────────────────────────────────────────────────┘
     [0;32m■[0m = Inside the shape
     [0;31m·[0m = Outside the shape
    [0m
    --- Processing Strategy ---[0m
    [0mUsing monthly dataset: True[0m
    [0mTotal months to process: 12[0m
    [0mMax months per chunk: 100[0m
    [0mNeeds chunking: False[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 14:54:27,165 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 14:54:28,165 INFO Request ID is a27c03c9-5918-4031-8ad7-9b1a41b1dcc6
    INFO:datapi.legacy_api_client:Request ID is a27c03c9-5918-4031-8ad7-9b1a41b1dcc6
    2025-07-15 14:54:28,395 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 14:54:37,917 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 14:54:43,149 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                            

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\test2.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\test2.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test2\data_stream-moda_stepType-avgad.nc[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test2\data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 2 file(s)[0m
    [0m  Processing file 1/2: data_stream-moda_stepType-avgad.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 12, 'latitude': 25, 'longitude': 73})[0m
    [0m  Processing file 2/2: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 12, 'latitude': 25, 'longitude': 73})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 1825 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m


    

    [0m✓ Coordinate filtering completed in 0.24 seconds[0m
    [0m  - Points inside: 962[0m
    [0m  - Points outside: 863[0m
    [0m  - Percentage inside: 52.71%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 43800 rows[0m
    [0m  ✓ Created lookup set with 962 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 43800 to 23088 rows[0m
    [0m✓ Dataset filtering completed in 0.04 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.29 seconds[0m
    [0mFinal DataFrame shape: (23088, 7)[0m
    [0mRows in final dataset: 23088[0m
    [0m[0;34mAGGREGATING DATA (MONTHLY)[0m[0m
    [0mAggregating data to monthly frequency...[0m
    [0mSum columns: ['tp'][0m
    [0mMax columns: [][0m
    [0mMin columns: [][0m
    [0mRate columns: [][0m
    [0mAverage columns: ['t2m'][0m
    [0mAggregation completed in:   0.02 seconds[0m
    [0m
    Saving files to output directory: test2_output[0m
    [0m  Saved final data to: test2_output\test2_monthly_data.csv[0m
    [0m  Saved unique coordinates to: test2_output\test2_unique_latlongs.csv[0m
    [0m  Saved raw data to: test2_output\test2_raw_data.csv[0m
    [0m
    ============================================================[0m
    [0m[0;32mPROCESSING COMPLETE[0m[0m
    [0m============================================================[0m
    [0m
    [0;36mRESULTS SUMMARY:[0m[0m
    [0m----------------------------------------[0m
    [0mVariables processed: 2[0m
    [0mTime period:         2024-01-01 to 2024-12-31[0m
    [0mFinal output shape:  (12, 4)[0m
    [0mTotal complete processing time: 20.73 seconds[0m
    [0m
    First 5 rows of aggregated data:[0m
    [0m         tp         t2m  year  month
    0  0.054632  267.574188  2024      1
    1  0.061895  273.594452  2024      2
    2  0.025322  276.579803  2024      3
    3  0.074519  280.693359  2024      4
    4  0.025147  287.699432  2024      5[0m
    [0m
    ============================================================[0m
    [0m[0;34mERA5 SINGLE LEVEL PROCESSING COMPLETED SUCCESSFULLY[0m[0m
    [0m============================================================[0m



```python
# varunayan.era5ify_bbox(request_id, variables, start_date, end_date, north, south, east, west, dataset_type, pressure_levels, frequency, resolution)
# request_id : str, unique identifier for the request
# variables : list, list of variables to download
# start_date : string, start date of the data ('YYYY-M-D' or 'YYYY-MM-DD')
# end_date : string, end date of the data ('YYYY-M-D' or 'YYYY-MM-DD')
# north : float, northern boundary of the bounding box
# south : float, southern boundary of the bounding box
# east : float, eastern boundary of the bounding box
# west : float, western boundary of the bounding box
# dataset_type : str, type of dataset (single or pressure, for single level or pressure level datasets), optional (single by default)
# pressure_levels : list, list of strings of pressure levels to download (e.g., ["1000", "925", "850"]), optional (empty by default)
# frequency : str, frequency of the data (hourly, daily, weekly, monthly, yearly), optional (hourly by default)
# resolution : float, resolution of the data in degrees (0.1, 0.25, etc.), optional (0.25 by default)
```


```python
df = varunayan.era5ify_bbox(
    request_id="test3",
    variables=[
        "2m_temperature", 
        "total_precipitation"
    ],
    start_date="2024-01-1",
    end_date="2024-01-15",
    north = 30,
    south = 20,
    east = 80,
    west = 70,
    frequency="daily",
    resolution=0.25
)
```

    [0m✓ CDS API configuration is already set up and valid.[0m
    [0m
    ============================================================[0m
    [0m[0;34mSTARTING ERA5 SINGLE LEVEL PROCESSING[0m[0m
    [0m============================================================[0m
    [0mRequest ID: test3[0m
    [0mVariables: ['2m_temperature', 'total_precipitation'][0m
    [0mDate Range: 2024-01-01 to 2024-01-15[0m
    [0mFrequency: daily[0m
    [0mResolution: 0.25°[0m
    [0m[0;32m✓ All inputs validated successfully[0m[0m
    [0m
    --- Bounding Box ---[0m
    [0m[0;32m✓ Bounding Box calculated:[0m[0m
    [0m  North: 30.0000°[0m
    [0m  South: 20.0000°[0m
    [0m  East:  80.0000°[0m
    [0m  West:  70.0000°[0m
    [0m  Area:  10.0000° × 10.0000°[0m
    [0m
    --- Processing Strategy ---[0m
    [0mUsing monthly dataset: False[0m
    [0mTotal days to process: 15[0m
    [0mMax days per chunk: 14[0m
    [0mNeeds chunking: True[0m
    [0m[0;36mPROCESSING CHUNK 1/2[0m
    Date Range: 2024-01-01 to 2024-01-14
    Variables:  2m_temperature, total_precipitation[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 14:54:52,562 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 14:54:53,379 INFO Request ID is 85c0b2ca-7654-4c11-88c5-ed0f8cb44edb
    INFO:datapi.legacy_api_client:Request ID is 85c0b2ca-7654-4c11-88c5-ed0f8cb44edb
    2025-07-15 14:54:53,520 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 14:55:02,451 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 14:55:07,717 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                             

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\test3_chunk1.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\test3_chunk1.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test3_chunk1\data_stream-oper_stepType-accum.nc[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test3_chunk1\data_stream-oper_stepType-instant.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 2 file(s)[0m
    [0m  Processing file 1/2: data_stream-oper_stepType-accum.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 336, 'latitude': 41, 'longitude': 41})[0m
    [0m  Processing file 2/2: data_stream-oper_stepType-instant.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 336, 'latitude': 41, 'longitude': 41})[0m


    

    [0m[0;32m✓ Chunk completed in 21.9 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 2/2[0m
    Date Range: 2024-01-15 to 2024-01-15
    Variables:  2m_temperature, total_precipitation[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 14:55:24,715 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 14:55:25,432 INFO Request ID is 61c9df68-17e6-4ba9-9e22-745f155d7e1e
    INFO:datapi.legacy_api_client:Request ID is 61c9df68-17e6-4ba9-9e22-745f155d7e1e
    2025-07-15 14:55:25,647 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 14:55:31,168 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 14:55:34,694 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                            

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\test3_chunk2.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\test3_chunk2.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test3_chunk2\data_stream-oper_stepType-accum.nc[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test3_chunk2\data_stream-oper_stepType-instant.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 2 file(s)[0m
    [0m  Processing file 1/2: data_stream-oper_stepType-accum.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 24, 'latitude': 41, 'longitude': 41})[0m
    [0m  Processing file 2/2: data_stream-oper_stepType-instant.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 24, 'latitude': 41, 'longitude': 41})[0m
    [0m[0;32m✓ Chunk completed in 14.1 seconds[0m[0m
    [0m[0;34mAGGREGATING DATA (DAILY)[0m[0m
    [0mAggregating data to daily frequency...[0m


    

    [0mSum columns: ['tp'][0m
    [0mMax columns: [][0m
    [0mMin columns: [][0m
    [0mRate columns: [][0m
    [0mAverage columns: ['t2m'][0m
    [0mAggregation completed in:   0.25 seconds[0m
    [0m
    Saving files to output directory: test3_output[0m
    [0m  Saved final data to: test3_output\test3_daily_data.csv[0m
    [0m  Saved unique coordinates to: test3_output\test3_unique_latlongs.csv[0m
    [0m  Saved raw data to: test3_output\test3_raw_data.csv[0m
    [0m
    ============================================================[0m
    [0m[0;32mPROCESSING COMPLETE[0m[0m
    [0m============================================================[0m
    [0m
    [0;36mRESULTS SUMMARY:[0m[0m
    [0m----------------------------------------[0m
    [0mVariables processed: 2[0m
    [0mTime period:         2024-01-01 to 2024-01-15[0m
    [0mFinal output shape:  (15, 6)[0m
    [0mTotal complete processing time: 51.17 seconds[0m
    [0m
    First 5 rows of aggregated data:[0m
    [0m         tp         t2m  year  month  day        date
    0  0.000059  289.480377  2024      1    1  2024-01-01
    1  0.000158  288.823975  2024      1    2  2024-01-02
    2  0.000437  288.676178  2024      1    3  2024-01-03
    3  0.000333  288.236481  2024      1    4  2024-01-04
    4  0.000649  288.469452  2024      1    5  2024-01-05[0m
    [0m
    ============================================================[0m
    [0m[0;34mERA5 SINGLE LEVEL PROCESSING COMPLETED SUCCESSFULLY[0m[0m
    [0m============================================================[0m



```python
df = varunayan.era5ify_bbox(
    request_id="test4",
    variables=[
        "temperature", 
        "relative_humidity"
    ],
    start_date="2024-01-1",
    end_date="2024-01-15",
    north = 30,
    south = 20,
    east = 80,
    west = 70,
    dataset_type="pressure",
    pressure_levels=["1000"],
    frequency="daily",
    resolution=0.25
)
```

    [0m✓ CDS API configuration is already set up and valid.[0m
    [0m
    ============================================================[0m
    [0m[0;34mSTARTING ERA5 PRESSURE LEVEL PROCESSING[0m[0m
    [0m============================================================[0m
    [0mRequest ID: test4[0m
    [0mVariables: ['temperature', 'relative_humidity'][0m
    [0mPressure Levels: ['1000'][0m
    [0mDate Range: 2024-01-01 to 2024-01-15[0m
    [0mFrequency: daily[0m
    [0mResolution: 0.25°[0m
    [0m[0;32m✓ All inputs validated successfully[0m[0m
    [0m
    --- Bounding Box ---[0m
    [0m[0;32m✓ Bounding Box calculated:[0m[0m
    [0m  North: 30.0000°[0m
    [0m  South: 20.0000°[0m
    [0m  East:  80.0000°[0m
    [0m  West:  70.0000°[0m
    [0m  Area:  10.0000° × 10.0000°[0m
    [0m
    --- Processing Strategy ---[0m
    [0mUsing monthly dataset: False[0m
    [0mTotal days to process: 15[0m
    [0mMax days per chunk: 14[0m
    [0mNeeds chunking: True[0m
    [0m[0;36mPROCESSING CHUNK 1/2[0m
    Date Range: 2024-01-01 to 2024-01-14
    Variables:  temperature, relative_humidity
    Levels:     1000[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 14:56:49,535 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 14:56:49,888 INFO Request ID is 62d7cf34-3c20-4a68-bdda-a49b53063f36
    INFO:datapi.legacy_api_client:Request ID is 62d7cf34-3c20-4a68-bdda-a49b53063f36
    2025-07-15 14:56:50,117 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 14:56:59,231 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                            

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\test4_chunk1.nc[0m[0m
    [0mCopying NetCDF file: C:\Users\ATHARV~1\AppData\Local\Temp\test4_chunk1.nc[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test4_chunk1\test4_chunk1.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: test4_chunk1.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 336, 'pressure_level': 1, 'latitude': 41, 'longitude': 41})[0m


    

    [0m[0;32m✓ Chunk completed in 25.0 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 2/2[0m
    Date Range: 2024-01-15 to 2024-01-15
    Variables:  temperature, relative_humidity
    Levels:     1000[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 14:57:23,400 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 14:57:24,217 INFO Request ID is 0d936ee2-30c9-444d-80f2-9cac36344542
    INFO:datapi.legacy_api_client:Request ID is 0d936ee2-30c9-444d-80f2-9cac36344542
    2025-07-15 14:57:24,457 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 14:57:29,953 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 14:57:33,649 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                          

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\test4_chunk2.nc[0m[0m
    [0mCopying NetCDF file: C:\Users\ATHARV~1\AppData\Local\Temp\test4_chunk2.nc[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test4_chunk2\test4_chunk2.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: test4_chunk2.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 24, 'pressure_level': 1, 'latitude': 41, 'longitude': 41})[0m
    [0m[0;32m✓ Chunk completed in 14.3 seconds[0m[0m
    [0m[0;34mAGGREGATING DATA (DAILY)[0m[0m
    [0mAggregating pressure level data to daily frequency...[0m
    [0mVariables to average: ['t', 'r'][0m
    [0mIncluding pressure_level in aggregation groups[0m
    [0mAggregation completed in:   0.08 seconds[0m
    [0m
    Saving files to output directory: test4_output[0m
    [0m  Saved final data to: test4_output\test4_daily_data.csv[0m


    

    [0m  Saved unique coordinates to: test4_output\test4_unique_latlongs.csv[0m
    [0m  Saved raw data to: test4_output\test4_raw_data.csv[0m
    [0m
    ============================================================[0m
    [0m[0;32mPROCESSING COMPLETE[0m[0m
    [0m============================================================[0m
    [0m
    [0;36mRESULTS SUMMARY:[0m[0m
    [0m----------------------------------------[0m
    [0mVariables processed: 2[0m
    [0mTime period:         2024-01-01 to 2024-01-15[0m
    [0mFinal output shape:  (15, 6)[0m
    [0mTotal complete processing time: 51.91 seconds[0m
    [0m
    First 5 rows of aggregated data:[0m
    [0m            t          r  pressure_level  year  month  day
    0  292.125336  72.452385          1000.0  2024      1    1
    1  291.697723  72.968575          1000.0  2024      1    2
    2  291.161835  74.767265          1000.0  2024      1    3
    3  291.061493  74.192192          1000.0  2024      1    4
    4  290.956696  73.344673          1000.0  2024      1    5[0m
    [0m
    ============================================================[0m
    [0m[0;34mERA5 PRESSURE LEVEL PROCESSING COMPLETED SUCCESSFULLY[0m[0m
    [0m============================================================[0m



```python
# varunayan.era5ify_point(request_id, variables, start_date, end_date, latitude, longitude, dataset_type, pressure_levels, frequency)
# request_id : str, unique identifier for the request
# variables : list, list of variables to download
# start_date : string, start date of the data ('YYYY-M-D' or 'YYYY-MM-DD')
# end_date : string, end date of the data ('YYYY-M-D' or 'YYYY-MM-DD')
# latitude : float, latitude of the point of interest
# longitude : float, longitude of the point of interest
# dataset_type : str, type of dataset (single or pressure, for single level or pressure level datasets), optional (single by default)
# pressure_levels : list, list of strings of pressure levels to download (e.g., ["1000", "925", "850"]), optional (empty by default)
# frequency : str, frequency of the data (hourly, daily, weekly, monthly, yearly), optional (hourly by default)
```


```python
df = varunayan.era5ify_point(
    request_id="test5",
    variables=[
        "2m_temperature", 
        "total_precipitation"
    ],
    start_date="2024-08-1",
    end_date="2024-08-14",
    latitude = 19.1331,
    longitude = 72.9151,
    frequency="daily",
    )
```

    [0m✓ CDS API configuration is already set up and valid.[0m
    [0m
    ============================================================[0m
    [0m[0;34mSTARTING ERA5 SINGLE LEVEL PROCESSING[0m[0m
    [0m============================================================[0m
    [0mRequest ID: test5[0m
    [0mVariables: ['2m_temperature', 'total_precipitation'][0m
    [0mDate Range: 2024-08-01 to 2024-08-14[0m
    [0mFrequency: daily[0m
    [0mResolution: 0.1°[0m
    [0mGeoJSON File: C:\Users\ATHARV~1\AppData\Local\Temp\test5_temp_geojson.json[0m
    [0m[0;32m✓ All inputs validated successfully[0m[0m
    [0m
    --- Bounding Box ---[0m
    [0m[0;32m✓ Bounding Box calculated:[0m[0m
    [0m  North: 19.1931°[0m
    [0m  South: 19.0731°[0m
    [0m  East:  72.9786°[0m
    [0m  West:  72.8516°[0m
    [0m  Area:  0.1270° × 0.1200°[0m


    
    
    --- GeoJSON Mini Map ---
    
    [0;34mMINI MAP (72.85°W to 72.98°E, 19.07°S to 19.19°N):[0m
    ┌─────────────────────────────────────────┐
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m│
    │[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m│
    │[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m│
    │[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m│
    │[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;32m■[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    │[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m[0;31m·[0m│
    └─────────────────────────────────────────┘
     [0;32m■[0m = Inside the shape
     [0;31m·[0m = Outside the shape
    [0m
    --- Processing Strategy ---[0m
    [0mUsing monthly dataset: False[0m
    [0mTotal days to process: 14[0m
    [0mMax days per chunk: 14[0m
    [0mNeeds chunking: False[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 14:57:49,375 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 14:57:50,332 INFO Request ID is 1d529c64-d82b-42a5-a8ac-0acce700e208
    INFO:datapi.legacy_api_client:Request ID is 1d529c64-d82b-42a5-a8ac-0acce700e208
    2025-07-15 14:57:50,490 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 14:57:59,545 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 14:58:05,074 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                            

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\test5.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\test5.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test5\data_stream-oper_stepType-accum.nc[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\test5\data_stream-oper_stepType-instant.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 2 file(s)[0m
    [0m  Processing file 1/2: data_stream-oper_stepType-accum.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 336, 'latitude': 2, 'longitude': 2})[0m
    [0m  Processing file 2/2: data_stream-oper_stepType-instant.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 336, 'latitude': 2, 'longitude': 2})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 4 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.00 seconds[0m
    [0m  - Points inside: 1[0m
    [0m  - Points outside: 3[0m
    [0m  - Percentage inside: 25.00%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1344 rows[0m
    [0m  ✓ Created lookup set with 1 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1344 to 336 rows[0m
    [0m✓ Dataset filtering completed in 0.01 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.02 seconds[0m
    [0mFinal DataFrame shape: (336, 7)[0m
    [0mRows in final dataset: 336[0m
    [0m[0;34mAGGREGATING DATA (DAILY)[0m[0m
    [0mAggregating data to daily frequency...[0m
    [0mSum columns: ['tp'][0m
    [0mMax columns: [][0m
    [0mMin columns: [][0m
    [0mRate columns: [][0m
    [0mAverage columns: ['t2m'][0m
    [0mAggregation completed in:   0.01 seconds[0m
    [0m
    Saving files to output directory: test5_output[0m
    [0m  Saved final data to: test5_output\test5_daily_data.csv[0m
    [0m  Saved unique coordinates to: test5_output\test5_unique_latlongs.csv[0m
    [0m  Saved raw data to: test5_output\test5_raw_data.csv[0m
    [0m
    ============================================================[0m
    [0m[0;32mPROCESSING COMPLETE[0m[0m
    [0m============================================================[0m
    [0m
    [0;36mRESULTS SUMMARY:[0m[0m
    [0m----------------------------------------[0m
    [0mVariables processed: 2[0m
    [0mTime period:         2024-08-01 to 2024-08-14[0m
    [0mFinal output shape:  (14, 6)[0m
    [0mTotal complete processing time: 20.34 seconds[0m
    [0m
    First 5 rows of aggregated data:[0m
    [0m         tp         t2m  year  month  day        date
    0  0.008118  300.662445  2024      8    1  2024-08-01
    1  0.013038  300.330231  2024      8    2  2024-08-02
    2  0.033061  300.136017  2024      8    3  2024-08-03
    3  0.041023  300.196167  2024      8    4  2024-08-04
    4  0.007252  300.486237  2024      8    5  2024-08-05[0m
    [0m
    ============================================================[0m
    [0m[0;34mERA5 SINGLE LEVEL PROCESSING COMPLETED SUCCESSFULLY[0m[0m
    [0m============================================================[0m


    


```python
# varunayan.search_variable(pattern, dataset_type)
# pattern : str, pattern to search for in variable names from dataset in dataset_type
# dataset_type :str,  Dataset type to search ("single", "pressure", "all", or any other registered dataset, all by dedault)
```


```python
varunayan.search_variable("teMp ", dataset_type="all")
```

    
    === SEARCH RESULTS (ALL LEVELS) ===
    Pattern: 'temp'
    Variables found: 21
    
    --- Temperature And Pressure ---
    1. 2m_dewpoint_temperature (from single levels)
       Description: Dew point temperature at 2 meters above the surface, representing the temperature at which air becomes saturated with moisture. Unit: Kelvin (K).
    
    2. 2m_temperature (from single levels)
       Description: Air temperature at 2 meters above the surface, typically used to represent surface-level weather conditions. Unit: Kelvin (K).
    
    3. ice_temperature_layer_1 (from single levels)
       Description: Temperature of the top layer of sea ice. This layer is most affected by atmospheric conditions. Unit: Kelvin (K).
    
    4. ice_temperature_layer_2 (from single levels)
       Description: Temperature of the second layer of sea ice, representing deeper internal ice temperatures. Unit: Kelvin (K).
    
    5. ice_temperature_layer_3 (from single levels)
       Description: Temperature of the third layer of sea ice, indicating mid-level internal ice temperature. Unit: Kelvin (K).
    
    6. ice_temperature_layer_4 (from single levels)
       Description: Temperature of the deepest (fourth) layer of sea ice, typically least affected by surface variations. Unit: Kelvin (K).
    
    7. maximum_2m_temperature_since_previous_post_processing (from single levels)
       Description: Maximum 2-meter air temperature recorded since the last post-processing cycle. Often used to estimate daily high temperature. Unit: Kelvin (K).
    
    8. minimum_2m_temperature_since_previous_post_processing (from single levels)
       Description: Minimum 2-meter air temperature recorded since the last post-processing cycle. Often used to estimate daily low temperature. Unit: Kelvin (K).
    
    9. sea_surface_temperature (from single levels)
       Description: Temperature of the ocean surface, typically the upper few millimeters. Important for weather forecasting and climate models. Unit: Kelvin (K).
    
    10. skin_temperature (from single levels)
       Description: Temperature of the Earth’s surface (land or sea) as perceived by a satellite sensor, also known as surface skin temperature. Unit: Kelvin (K).
    
    
    --- Lake Variables ---
    1. lake_bottom_temperature (from single levels)
       Description: Temperature at the bottom layer of the lake. Reflects long-term thermal state. Unit: Kelvin (K).
    
    2. lake_ice_temperature (from single levels)
       Description: Temperature of the lake's ice layer. Unit: Kelvin (K).
    
    3. lake_mix_layer_temperature (from single levels)
       Description: Temperature of the mixed layer in the lake. Unit: Kelvin (K).
    
    4. lake_total_layer_temperature (from single levels)
       Description: Average temperature of the entire lake water column. Unit: Kelvin (K).
    
    
    --- Snow Variables ---
    1. temperature_of_snow_layer (from single levels)
       Description: Temperature of the snow layer at the surface. Unit: Kelvin (K).
    
    
    --- Soil Variables ---
    1. soil_temperature_level_1 (from single levels)
       Description: Soil temperature in the topmost layer (0–7 cm). Unit: Kelvin (K).
    
    2. soil_temperature_level_2 (from single levels)
       Description: Soil temperature in the second layer (7–28 cm). Unit: Kelvin (K).
    
    3. soil_temperature_level_3 (from single levels)
       Description: Soil temperature in the third layer (28–100 cm). Unit: Kelvin (K).
    
    4. soil_temperature_level_4 (from single levels)
       Description: Soil temperature in the deepest layer (100–289 cm). Unit: Kelvin (K).
    
    
    --- Vertical Integral Variables ---
    1. vertical_integral_of_temperature (from single levels)
       Description: Vertical integral of temperature over atmospheric column. Unit: K·m
    
    
    --- Pressure Levels ---
    1. temperature (from pressure levels)
       Description: Air temperature at pressure level. Unit: K
    



```python
# varunayan.describe_variables(variable_names, dataset_type)
# variable_names : list, list of variable names to describe
# dataset_type : str, type of dataset (single or pressure, for single level or pressure level datasets)
```


```python
varunayan.describe_variables(
    variable_names=["2m_temperature", "total_precipitation", "surface_pressure"], dataset_type="single"
)
```

    
    === Variable Descriptions (SINGLE LEVELS) ===
    
    2m_temperature:
      Category: temperature_and_pressure
      Description: Air temperature at 2 meters above the surface, typically used to represent surface-level weather conditions. Unit: Kelvin (K).
    
    total_precipitation:
      Category: precipitation_variables
      Description: Cumulative precipitation (convective + large-scale). Unit: meters (m) of water equivalent.
    
    surface_pressure:
      Category: temperature_and_pressure
      Description: Atmospheric pressure at the surface of the Earth. Influenced by elevation and weather systems. Unit: Pascal (Pa).

