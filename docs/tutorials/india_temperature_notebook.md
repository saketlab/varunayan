```python
import varunayan
```


```python
df = varunayan.era5ify_geojson(request_id="temp_india_yearly", 
                             variables=["2m_temperature"],
                             start_date="1941-1-1",
                             end_date="2024-12-31",
                             json_file="../data/india.json",
                             frequency="yearly")
```

    [0m✓ CDS API configuration is already set up and valid.[0m
    [0m
    ============================================================[0m
    [0m[0;34mSTARTING ERA5 SINGLE LEVEL PROCESSING[0m[0m
    [0m============================================================[0m
    [0mRequest ID: temp_india_yearly[0m
    [0mVariables: ['2m_temperature'][0m
    [0mDate Range: 1941-01-01 to 2024-12-31[0m
    [0mFrequency: yearly[0m
    [0mResolution: 0.25°[0m
    [0mGeoJSON File: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_temp_geojson.json[0m
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
    [0mUsing monthly dataset: True[0m
    [0mTotal months to process: 1008[0m
    [0mMax months per chunk: 100[0m
    [0mNeeds chunking: True[0m
    [0m[0;36mPROCESSING CHUNK 1/11[0m
    Date Range: 1941-01-01 to 1949-04-30
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 14:58:44,807 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 14:58:45,625 INFO Request ID is 881d52bd-66ca-40de-8d8c-91d35a5e602a
    INFO:datapi.legacy_api_client:Request ID is 881d52bd-66ca-40de-8d8c-91d35a5e602a
    2025-07-15 14:58:45,831 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 14:58:54,944 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 14:59:08,054 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                              

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk1.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk1.zip[0m
    [0mExtracted NetCDF files:[0m


    

    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk1\data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.86 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 1.32 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 2.21 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 30.5 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 2/11[0m
    Date Range: 1949-05-01 to 1957-08-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 14:59:25,417 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 14:59:26,485 INFO Request ID is afd60d9b-f6fc-4aed-acf9-d100ebd3193d
    INFO:datapi.legacy_api_client:Request ID is afd60d9b-f6fc-4aed-acf9-d100ebd3193d
    2025-07-15 14:59:26,894 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 14:59:36,078 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 15:00:00,916 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                             

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk2.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk2.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk2\data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m


    

    [0m✓ Coordinate filtering completed in 1.18 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 1.52 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 2.72 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 48.3 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 3/11[0m
    Date Range: 1957-09-01 to 1965-12-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 15:00:26,799 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 15:00:27,523 INFO Request ID is fd0039c0-d411-4a9c-a206-edd24e0ab967
    INFO:datapi.legacy_api_client:Request ID is fd0039c0-d411-4a9c-a206-edd24e0ab967
    2025-07-15 15:00:27,903 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 15:00:33,730 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 15:00:50,379 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                             

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk3.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk3.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk3\data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m


    

    [0m✓ Coordinate filtering completed in 0.78 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 1.06 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 1.86 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 44.0 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 4/11[0m
    Date Range: 1966-01-01 to 1974-04-30
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 15:01:17,966 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 15:01:18,482 INFO Request ID is 0b1bcf05-207b-45da-8b76-5c7d4e418841
    INFO:datapi.legacy_api_client:Request ID is 0b1bcf05-207b-45da-8b76-5c7d4e418841
    2025-07-15 15:01:18,716 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 15:01:28,136 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 15:01:41,359 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                              

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk4.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk4.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk4\data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m


    

    [0m✓ Coordinate filtering completed in 0.84 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 1.16 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 2.02 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 53.5 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 5/11[0m
    Date Range: 1974-05-01 to 1982-08-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 15:02:21,385 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 15:02:22,652 INFO Request ID is ad206152-393e-41e7-a03c-93a7b2acae95
    INFO:datapi.legacy_api_client:Request ID is ad206152-393e-41e7-a03c-93a7b2acae95
    2025-07-15 15:02:22,819 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 15:02:31,831 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 15:02:45,143 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                             

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk5.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk5.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk5\data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m


    

    [0m✓ Coordinate filtering completed in 0.68 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 1.12 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 1.81 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 46.1 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 6/11[0m
    Date Range: 1982-09-01 to 1990-12-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 15:03:17,298 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 15:03:18,320 INFO Request ID is 1bf3e205-539b-41eb-848e-99ebe56aa890
    INFO:datapi.legacy_api_client:Request ID is 1bf3e205-539b-41eb-848e-99ebe56aa890
    2025-07-15 15:03:18,526 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 15:03:33,048 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 15:03:53,342 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                             

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk6.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk6.zip[0m
    [0mExtracted NetCDF files:[0m


    

    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk6\data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 1.05 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 1.25 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 2.33 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 45.3 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 7/11[0m
    Date Range: 1991-01-01 to 1999-04-30
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 15:04:12,698 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 15:04:13,313 INFO Request ID is 68980586-deec-4dfd-85e4-0eed0095a4a9
    INFO:datapi.legacy_api_client:Request ID is 68980586-deec-4dfd-85e4-0eed0095a4a9
    2025-07-15 15:04:13,515 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 15:04:24,439 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 15:04:29,806 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 15:04:37,580 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 15:04:50,073 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                             

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk7.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk7.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk7\data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m


    

    [0m✓ Coordinate filtering completed in 0.93 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 1.25 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 2.20 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 48.4 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 8/11[0m
    Date Range: 1999-05-01 to 2007-08-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 15:05:11,066 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 15:05:11,783 INFO Request ID is 22bbc3cf-60da-4062-836a-7ff6e8686579
    INFO:datapi.legacy_api_client:Request ID is 22bbc3cf-60da-4062-836a-7ff6e8686579
    2025-07-15 15:05:11,987 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 15:05:21,202 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 15:05:35,540 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                             

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk8.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk8.zip[0m
    [0mExtracted NetCDF files:[0m


    

    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk8\data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.91 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 1.19 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 2.11 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 33.6 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 9/11[0m
    Date Range: 2007-09-01 to 2015-12-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 15:05:55,508 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 15:05:56,224 INFO Request ID is 00aeff33-7f26-455a-9bd2-c352330e160e
    INFO:datapi.legacy_api_client:Request ID is 00aeff33-7f26-455a-9bd2-c352330e160e
    2025-07-15 15:05:56,428 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 15:06:05,338 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 15:06:30,834 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                             

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk9.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk9.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk9\data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m


    

    [0m✓ Coordinate filtering completed in 1.05 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 1.48 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 2.55 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 49.3 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 10/11[0m
    Date Range: 2016-01-01 to 2024-04-30
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 15:06:54,285 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 15:06:54,902 INFO Request ID is 8a6c0591-0e77-4372-abd5-67db320f68d1
    INFO:datapi.legacy_api_client:Request ID is 8a6c0591-0e77-4372-abd5-67db320f68d1
    2025-07-15 15:06:55,105 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 15:07:04,325 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 15:07:17,331 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                             

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk10.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk10.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk10\data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m


    

    [0m✓ Coordinate filtering completed in 1.03 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 1.39 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 2.43 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 36.4 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 11/11[0m
    Date Range: 2024-05-01 to 2024-12-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 15:07:40,366 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:datapi.legacy_api_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 15:07:41,204 INFO Request ID is fcf37c79-7b5b-4162-b4db-0b04fa2c16ca
    INFO:datapi.legacy_api_client:Request ID is fcf37c79-7b5b-4162-b4db-0b04fa2c16ca
    2025-07-15 15:07:41,391 INFO status has been updated to accepted
    INFO:datapi.legacy_api_client:status has been updated to accepted
    2025-07-15 15:07:56,341 INFO status has been updated to running
    INFO:datapi.legacy_api_client:status has been updated to running
    2025-07-15 15:08:04,125 INFO status has been updated to successful
    INFO:datapi.legacy_api_client:status has been updated to successful
                                                                                            

    [0m  [0;32m✓ Download completed: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk11.zip[0m[0m
    [0mExtracting zip file: C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk11.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - C:\Users\ATHARV~1\AppData\Local\Temp\temp_india_yearly_chunk11\data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 8, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m


    

    [0m✓ Coordinate filtering completed in 1.01 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 103896 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 103896 to 35568 rows[0m
    [0m✓ Dataset filtering completed in 0.11 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 1.14 seconds[0m
    [0mFinal DataFrame shape: (35568, 6)[0m
    [0mRows in final dataset: 35568[0m
    [0m[0;32m✓ Chunk completed in 31.0 seconds[0m[0m
    [0m[0;34mAGGREGATING DATA (YEARLY)[0m[0m
    [0mAggregating data to yearly frequency...[0m
    [0mSum columns: [][0m
    [0mMax columns: [][0m
    [0mMin columns: [][0m
    [0mRate columns: [][0m
    [0mAverage columns: ['t2m'][0m
    [0mAggregation completed in:   1.66 seconds[0m
    [0m
    Saving files to output directory: temp_india_yearly_output[0m
    [0m  Saved final data to: temp_india_yearly_output\temp_india_yearly_yearly_data.csv[0m
    [0m  Saved unique coordinates to: temp_india_yearly_output\temp_india_yearly_unique_latlongs.csv[0m


    D:\varunayan\varunayan\processing\data_aggregator.py:195: FutureWarning: 'AS' is deprecated and will be removed in a future version, please use 'YS' instead.
      result[col] = spatial_agg[col].resample(freq_map[frequency]).mean()


    [0m  Saved raw data to: temp_india_yearly_output\temp_india_yearly_raw_data.csv[0m
    [0m
    ============================================================[0m
    [0m[0;32mPROCESSING COMPLETE[0m[0m
    [0m============================================================[0m
    [0m
    [0;36mRESULTS SUMMARY:[0m[0m
    [0m----------------------------------------[0m
    [0mVariables processed: 1[0m
    [0mTime period:         1941-01-01 to 2024-12-31[0m
    [0mFinal output shape:  (84, 2)[0m
    [0mTotal complete processing time: 602.30 seconds[0m
    [0m
    First 5 rows of aggregated data:[0m
    [0m          t2m  year
    0  296.386200  1941
    1  296.234344  1942
    2  295.743408  1943
    3  296.361176  1944
    4  296.111603  1945[0m
    [0m
    ============================================================[0m
    [0m[0;34mERA5 SINGLE LEVEL PROCESSING COMPLETED SUCCESSFULLY[0m[0m
    [0m============================================================[0m



```python
mean_t2m = df['t2m'].mean()

df['dev'] = df['t2m'] - mean_t2m

df.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>t2m</th>
      <th>year</th>
      <th>dev</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>296.386200</td>
      <td>1941</td>
      <td>-0.202301</td>
    </tr>
    <tr>
      <th>1</th>
      <td>296.234344</td>
      <td>1942</td>
      <td>-0.354156</td>
    </tr>
    <tr>
      <th>2</th>
      <td>295.743408</td>
      <td>1943</td>
      <td>-0.845093</td>
    </tr>
    <tr>
      <th>3</th>
      <td>296.361176</td>
      <td>1944</td>
      <td>-0.227325</td>
    </tr>
    <tr>
      <th>4</th>
      <td>296.111603</td>
      <td>1945</td>
      <td>-0.476898</td>
    </tr>
  </tbody>
</table>
</div>




```python
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
```


```python
norm = mcolors.Normalize(vmin=df['dev'].min(), vmax=df['dev'].max())
```


```python
cmap = plt.colormaps['coolwarm']
```


```python
colors = cmap(norm(df['dev']))
```


```python
fig, ax = plt.subplots(figsize=(14, 6))
bars = ax.bar(df['year'], df['dev'], color=colors)

sm = cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array(df['dev'].values)

cbar = fig.colorbar(sm, ax=ax)
cbar.set_label('Deviation')

ax.set_xlabel('Year')
ax.set_ylabel('Deviation')
ax.set_title('Temperature change in India')

plt.tight_layout()
plt.show()
```


    
![png](india_temperature_notebook_files/india_temperature_notebook_7_0.png)
    

