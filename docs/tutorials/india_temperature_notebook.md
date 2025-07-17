# Visualising climate change in India

In this vignette, we demonstrate the use of varunayan for visualizsing the change in average temeperatre from 1941 to 2024.



```python
import varunayan

df = varunayan.era5ify_geojson(
    request_id="temp_india_yearly",
    variables=["2m_temperature"],
    start_date="1941-1-1",
    end_date="2024-12-31",
    json_file="../data/india.json",
    frequency="yearly",
)
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
    [0mGeoJSON File: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_temp_geojson.json[0m
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


    2025-07-15 23:33:50,711 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:33:52,157 INFO Request ID is 47cf0915-4597-42ef-ac93-f710394b0d89
    INFO:ecmwf.datastores.legacy_client:Request ID is 47cf0915-4597-42ef-ac93-f710394b0d89
    2025-07-15 23:33:52,367 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:34:01,511 INFO status has been updated to running
    INFO:ecmwf.datastores.legacy_client:status has been updated to running
    2025-07-15 23:34:06,756 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    11816a5996f2ad50a927f9c906761429.zip:   0%|          | 0.00/2.29M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk1.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk1.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk1/data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.06 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 0.64 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.71 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 23.4 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 2/11[0m
    Date Range: 1949-05-01 to 1957-08-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:34:24,183 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:34:24,875 INFO Request ID is 4d66e7f1-184f-4e6c-8a1f-42b356508e71
    INFO:ecmwf.datastores.legacy_client:Request ID is 4d66e7f1-184f-4e6c-8a1f-42b356508e71
    2025-07-15 23:34:25,128 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:34:31,090 INFO status has been updated to running
    INFO:ecmwf.datastores.legacy_client:status has been updated to running
    2025-07-15 23:34:34,652 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    e0a0ebf7450e58d35c26985e9ffdf5d2.zip:   0%|          | 0.00/2.29M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk2.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk2.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk2/data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.08 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 0.57 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.66 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 15.9 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 3/11[0m
    Date Range: 1957-09-01 to 1965-12-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:34:49,959 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:34:51,254 INFO Request ID is 30700db7-a0fc-42b2-800b-ad235716167f
    INFO:ecmwf.datastores.legacy_client:Request ID is 30700db7-a0fc-42b2-800b-ad235716167f
    2025-07-15 23:34:51,417 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:35:00,202 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    684289f83f9ec5a445f2777d12466f59.zip:   0%|          | 0.00/2.28M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk3.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk3.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk3/data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.07 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 0.65 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.73 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 14.4 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 4/11[0m
    Date Range: 1966-01-01 to 1974-04-30
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:35:17,496 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:35:18,091 INFO Request ID is c76ad795-1761-40e2-9cd8-e6a36738f3a9
    INFO:ecmwf.datastores.legacy_client:Request ID is c76ad795-1761-40e2-9cd8-e6a36738f3a9
    2025-07-15 23:35:18,344 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:35:40,238 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    412b00c7f5eee84fe077883928bc2829.zip:   0%|          | 0.00/2.29M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk4.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk4.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk4/data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.08 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 0.59 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.67 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 29.4 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 5/11[0m
    Date Range: 1974-05-01 to 1982-08-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:35:53,731 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:35:54,309 INFO Request ID is 91a77c4e-97b6-44b6-86e4-09c112f8fcff
    INFO:ecmwf.datastores.legacy_client:Request ID is 91a77c4e-97b6-44b6-86e4-09c112f8fcff
    2025-07-15 23:35:54,485 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:36:08,576 INFO status has been updated to running
    INFO:ecmwf.datastores.legacy_client:status has been updated to running
    2025-07-15 23:36:27,908 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    435c337616af70ed2ba0251618388fdd.zip:   0%|          | 0.00/2.29M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk5.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk5.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk5/data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.13 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 0.62 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.77 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 38.1 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 6/11[0m
    Date Range: 1982-09-01 to 1990-12-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:36:41,825 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:36:42,318 INFO Request ID is 83df80d9-5c9f-4eb6-bab3-89755ba78a55
    INFO:ecmwf.datastores.legacy_client:Request ID is 83df80d9-5c9f-4eb6-bab3-89755ba78a55
    2025-07-15 23:36:42,464 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:36:51,792 INFO status has been updated to running
    INFO:ecmwf.datastores.legacy_client:status has been updated to running
    2025-07-15 23:37:04,770 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    c03c5d2fe3a0462c9c84d90e39f9a850.zip:   0%|          | 0.00/2.29M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk6.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk6.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk6/data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.07 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 0.69 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.77 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 28.6 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 7/11[0m
    Date Range: 1991-01-01 to 1999-04-30
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:37:20,456 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:37:21,032 INFO Request ID is 658e8e96-7eb3-4611-8f5e-0c8830349a4c
    INFO:ecmwf.datastores.legacy_client:Request ID is 658e8e96-7eb3-4611-8f5e-0c8830349a4c
    2025-07-15 23:37:21,205 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:37:30,042 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    cd6900b6c23a704f4e7066e4233b5242.zip:   0%|          | 0.00/2.29M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk7.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk7.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk7/data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.07 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 0.68 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.76 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 13.3 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 8/11[0m
    Date Range: 1999-05-01 to 2007-08-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:37:43,683 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:37:44,773 INFO Request ID is 602dd05b-304b-4bb9-8831-538b32dbd1bd
    INFO:ecmwf.datastores.legacy_client:Request ID is 602dd05b-304b-4bb9-8831-538b32dbd1bd
    2025-07-15 23:37:44,917 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:37:53,697 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    9d5648bc4e64a705ffab07909854d4a6.zip:   0%|          | 0.00/2.29M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk8.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk8.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk8/data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.07 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 0.71 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.79 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 13.5 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 9/11[0m
    Date Range: 2007-09-01 to 2015-12-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:38:07,216 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:38:07,934 INFO Request ID is 2cc1fb0b-d97a-40ab-8829-1b8479c208fd
    INFO:ecmwf.datastores.legacy_client:Request ID is 2cc1fb0b-d97a-40ab-8829-1b8479c208fd
    2025-07-15 23:38:08,113 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:38:22,278 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    d5e88404acc5259c4dec5904a8b420ef.zip:   0%|          | 0.00/2.28M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk9.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk9.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk9/data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.07 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 0.65 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.73 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 19.3 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 10/11[0m
    Date Range: 2016-01-01 to 2024-04-30
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:38:36,540 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:38:37,300 INFO Request ID is 47ea4164-9a66-44c9-ac18-0df7b4522802
    INFO:ecmwf.datastores.legacy_client:Request ID is 47ea4164-9a66-44c9-ac18-0df7b4522802
    2025-07-15 23:38:37,481 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:38:46,402 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    316b09b4161591ccc0a3a1ac059b2348.zip:   0%|          | 0.00/2.28M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk10.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk10.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk10/data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 108, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.08 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 1402596 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 1402596 to 480168 rows[0m
    [0m✓ Dataset filtering completed in 0.63 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.72 seconds[0m
    [0mFinal DataFrame shape: (480168, 6)[0m
    [0mRows in final dataset: 480168[0m
    [0m[0;32m✓ Chunk completed in 13.5 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 11/11[0m
    Date Range: 2024-05-01 to 2024-12-31
    Variables:  2m_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:39:00,230 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:39:01,190 INFO Request ID is 53b0a435-6236-443f-a188-6fa501fbe71c
    INFO:ecmwf.datastores.legacy_client:Request ID is 53b0a435-6236-443f-a188-6fa501fbe71c
    2025-07-15 23:39:01,497 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:39:07,433 INFO status has been updated to running
    INFO:ecmwf.datastores.legacy_client:status has been updated to running
    2025-07-15 23:39:11,042 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    f81da4a5487d6f886abf9d3c3b5aedac.zip:   0%|          | 0.00/195k [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk11.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk11.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_india_yearly_chunk11/data_stream-moda_stepType-avgua.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: data_stream-moda_stepType-avgua.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 8, 'latitude': 111, 'longitude': 117})[0m
    [0mStarting optimized filtering process...[0m
    [0m→ Extracting unique lat/lon coordinates from dataset...[0m
    [0m✓ Found 12987 unique lat/lon combinations[0m
    [0m→ Filtering unique coordinates against polygon...[0m
    [0m✓ Coordinate filtering completed in 0.07 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 103896 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 103896 to 35568 rows[0m
    [0m✓ Dataset filtering completed in 0.06 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.14 seconds[0m
    [0mFinal DataFrame shape: (35568, 6)[0m
    [0mRows in final dataset: 35568[0m
    [0m[0;32m✓ Chunk completed in 13.5 seconds[0m[0m
    [0m[0;34mAGGREGATING DATA (YEARLY)[0m[0m
    [0mAggregating data to yearly frequency...[0m
    [0mSum columns: [][0m
    [0mMax columns: [][0m
    [0mMin columns: [][0m
    [0mRate columns: [][0m
    [0mAverage columns: ['t2m'][0m
    [0mAggregation completed in:   0.77 seconds[0m
    [0m
    Saving files to output directory: temp_india_yearly_output[0m
    [0m  Saved final data to: temp_india_yearly_output/temp_india_yearly_yearly_data.csv[0m
    [0m  Saved unique coordinates to: temp_india_yearly_output/temp_india_yearly_unique_latlongs.csv[0m
    [0m  Saved raw data to: temp_india_yearly_output/temp_india_yearly_raw_data.csv[0m
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
    [0mTotal complete processing time: 337.14 seconds[0m
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
mean_t2m = df["t2m"].mean()

df["dev"] = df["t2m"] - mean_t2m

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
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt


def setup_matplotlib():
    plt.rcParams["figure.dpi"] = 300
    plt.rcParams["savefig.dpi"] = 300
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Arial"]
    plt.rcParams["axes.labelweight"] = "normal"

    plt.rcParams["mathtext.fontset"] = "custom"
    plt.rcParams["mathtext.rm"] = "Arial"
    plt.rcParams["mathtext.it"] = "Arial:italic"
    plt.rcParams["mathtext.bf"] = "Arial:bold"


setup_matplotlib()
```


```python
norm = mcolors.Normalize(vmin=df["dev"].min(), vmax=df["dev"].max())
```


```python
cmap = plt.colormaps["coolwarm"]
```


```python
colors = cmap(norm(df["dev"]))
```


```python
fig, ax = plt.subplots(figsize=(14, 6))
bars = ax.bar(df["year"], df["dev"], color=colors)

sm = cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array(df["dev"].values)

cbar = fig.colorbar(sm, ax=ax)
cbar.set_label("Deviation")

ax.set_xlabel("Year")
ax.set_ylabel("Deviation")
ax.set_title("Temperature change in India")

plt.tight_layout()
plt.show()
```


    
![png](india_temperature_notebook_files/india_temperature_notebook_7_0.png)
    

