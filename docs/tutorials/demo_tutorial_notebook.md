# Varunayan Demo

Varunayan =  Varun + ayan

Varun in the vedic mythology was the god of sky, order, truth, water and magic. 

Ayan in sanskrit means path.

Varunayan is a structured package for fetching climatic variables for any part of the globe, though not magically. Varunayan heavily relies on the  [ERA5](https://www.ecmwf.int/en/forecasts/dataset/ecmwf-reanalysis-v5) resource which uses advanced modeling using historical data to generate global estimates of large number of atmospheric, land and oceanic climate variables.


```python
import varunayan
```
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
## Download daily weather data for a given geojson

We will use varunayan to first download temperature, precipitation, surface pressure and dewpoint from [ERA5](https://www.ecmwf.int/en/forecasts/dataset/ecmwf-reanalysis-v5).

The location is specified using path to a local geojson file, though this is not the only way to download data for a desired geography (See next section).


```python
df_india = varunayan.era5ify_geojson(
    request_id="india_weather_daily_2023_Jan",
    variables=[
        "2m_temperature",
        "total_precipitation",
        "surface_pressure",
        "2m_dewpoint_temperature",
    ],
    start_date="2023-1-1",
    end_date="2023-1-31",
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
    [0mRequest ID: india_weather_daily_2023_Jan[0m
    [0mVariables: ['2m_temperature', 'total_precipitation', 'surface_pressure', '2m_dewpoint_temperature'][0m
    [0mDate Range: 2023-01-01 to 2023-01-31[0m
    [0mFrequency: daily[0m
    [0mResolution: 0.25°[0m
    [0mGeoJSON File: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/india_weather_daily_2023_Jan_temp_geojson.json[0m
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
    [0mTotal days to process: 31[0m
    [0mMax days per chunk: 14[0m
    [0mNeeds chunking: True[0m
    [0m[0;36mPROCESSING CHUNK 1/3[0m
    Date Range: 2023-01-01 to 2023-01-14
    Variables:  2m_temperature, total_precipitation, surface_pressure, 2m_dewpoint_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:23:54,646 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:23:55,456 INFO Request ID is a19c6db8-82ca-4f5e-ac25-6972debd8047
    INFO:ecmwf.datastores.legacy_client:Request ID is a19c6db8-82ca-4f5e-ac25-6972debd8047
    2025-07-15 23:23:55,660 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:24:04,523 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    c0420f38a4442a37ac07fbfed289a137.zip:   0%|          | 0.00/23.4M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/india_weather_daily_2023_Jan_chunk1.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/india_weather_daily_2023_Jan_chunk1.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/india_weather_daily_2023_Jan_chunk1/data_stream-oper_stepType-accum.nc[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/india_weather_daily_2023_Jan_chunk1/data_stream-oper_stepType-instant.nc[0m
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
    [0m✓ Coordinate filtering completed in 0.06 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 4363632 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 4363632 to 1493856 rows[0m
    [0m✓ Dataset filtering completed in 2.04 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 2.12 seconds[0m
    [0mFinal DataFrame shape: (1493856, 9)[0m
    [0mRows in final dataset: 1493856[0m
    [0m[0;32m✓ Chunk completed in 20.5 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 2/3[0m
    Date Range: 2023-01-15 to 2023-01-28
    Variables:  2m_temperature, total_precipitation, surface_pressure, 2m_dewpoint_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:24:25,991 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:24:26,590 INFO Request ID is de211f61-bcb0-4228-bfcd-e3ee08cbd8fc
    INFO:ecmwf.datastores.legacy_client:Request ID is de211f61-bcb0-4228-bfcd-e3ee08cbd8fc
    2025-07-15 23:24:26,741 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:24:35,563 INFO status has been updated to running
    INFO:ecmwf.datastores.legacy_client:status has been updated to running
    2025-07-15 23:24:48,536 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    aaeabb16743ab3aab9852ac0c019e719.zip:   0%|          | 0.00/23.2M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/india_weather_daily_2023_Jan_chunk2.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/india_weather_daily_2023_Jan_chunk2.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/india_weather_daily_2023_Jan_chunk2/data_stream-oper_stepType-accum.nc[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/india_weather_daily_2023_Jan_chunk2/data_stream-oper_stepType-instant.nc[0m
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
    [0m✓ Coordinate filtering completed in 0.07 seconds[0m
    [0m  - Points inside: 4446[0m
    [0m  - Points outside: 8541[0m
    [0m  - Percentage inside: 34.23%[0m
    [0m→ Filtering original dataset using inside coordinates...[0m
    [0m  Converting dataset to DataFrame...[0m
    [0m  ✓ Converted to DataFrame with 4363632 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 4363632 to 1493856 rows[0m
    [0m✓ Dataset filtering completed in 2.11 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 2.20 seconds[0m
    [0mFinal DataFrame shape: (1493856, 9)[0m
    [0mRows in final dataset: 1493856[0m
    [0m[0;32m✓ Chunk completed in 35.8 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 3/3[0m
    Date Range: 2023-01-29 to 2023-01-31
    Variables:  2m_temperature, total_precipitation, surface_pressure, 2m_dewpoint_temperature[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:25:11,052 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:25:12,030 INFO Request ID is 67fa536c-0fc0-48a6-abfb-10ee304f918f
    INFO:ecmwf.datastores.legacy_client:Request ID is 67fa536c-0fc0-48a6-abfb-10ee304f918f
    2025-07-15 23:25:12,913 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:25:18,330 INFO status has been updated to running
    INFO:ecmwf.datastores.legacy_client:status has been updated to running
    2025-07-15 23:25:21,939 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    858aa1485ddb20de4f449be065ac301a.zip:   0%|          | 0.00/5.15M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/india_weather_daily_2023_Jan_chunk3.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/india_weather_daily_2023_Jan_chunk3.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/india_weather_daily_2023_Jan_chunk3/data_stream-oper_stepType-accum.nc[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/india_weather_daily_2023_Jan_chunk3/data_stream-oper_stepType-instant.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 2 file(s)[0m
    [0m  Processing file 1/2: data_stream-oper_stepType-accum.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 72, 'latitude': 111, 'longitude': 117})[0m
    [0m  Processing file 2/2: data_stream-oper_stepType-instant.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 72, 'latitude': 111, 'longitude': 117})[0m
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
    [0m  ✓ Converted to DataFrame with 935064 rows[0m
    [0m  ✓ Created lookup set with 4446 coordinate pairs[0m
    [0m  Filtering DataFrame rows...[0m
    [0m  ✓ Filtered from 935064 to 320112 rows[0m
    [0m✓ Dataset filtering completed in 0.44 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.52 seconds[0m
    [0mFinal DataFrame shape: (320112, 9)[0m
    [0mRows in final dataset: 320112[0m
    [0m[0;32m✓ Chunk completed in 15.0 seconds[0m[0m
    [0m[0;34mAGGREGATING DATA (DAILY)[0m[0m
    [0mAggregating data to daily frequency...[0m
    [0mSum columns: ['tp'][0m
    [0mMax columns: [][0m
    [0mMin columns: [][0m
    [0mRate columns: [][0m
    [0mAverage columns: ['t2m', 'sp', 'd2m'][0m
    [0mAggregation completed in:   0.55 seconds[0m
    [0m
    Saving files to output directory: india_weather_daily_2023_Jan_output[0m
    [0m  Saved final data to: india_weather_daily_2023_Jan_output/india_weather_daily_2023_Jan_daily_data.csv[0m
    [0m  Saved unique coordinates to: india_weather_daily_2023_Jan_output/india_weather_daily_2023_Jan_unique_latlongs.csv[0m
    [0m  Saved raw data to: india_weather_daily_2023_Jan_output/india_weather_daily_2023_Jan_raw_data.csv[0m
    [0m
    ============================================================[0m
    [0m[0;32mPROCESSING COMPLETE[0m[0m
    [0m============================================================[0m
    [0m
    [0;36mRESULTS SUMMARY:[0m[0m
    [0m----------------------------------------[0m
    [0mVariables processed: 4[0m
    [0mTime period:         2023-01-01 to 2023-01-31[0m
    [0mFinal output shape:  (31, 8)[0m
    [0mTotal complete processing time: 105.64 seconds[0m
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
## Download daily weather data for a bounding box

The location can alternatively also be specified using a bounding box:


```python
df_bounding_box = varunayan.era5ify_bbox(
    request_id="temp_prec_bounding_box_2024",
    variables=["2m_temperature", "total_precipitation"],
    start_date="2024-01-1",
    end_date="2024-01-15",
    north=30,
    south=20,
    east=80,
    west=70,
    frequency="daily",
    resolution=0.25,
)
```

    [0m✓ CDS API configuration is already set up and valid.[0m
    [0m
    ============================================================[0m
    [0m[0;34mSTARTING ERA5 SINGLE LEVEL PROCESSING[0m[0m
    [0m============================================================[0m
    [0mRequest ID: temp_prec_bounding_box_2024[0m
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


    2025-07-15 23:25:40,242 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:25:41,028 INFO Request ID is b1e570e4-9cc4-4544-b04f-9b3ed78cb087
    INFO:ecmwf.datastores.legacy_client:Request ID is b1e570e4-9cc4-4544-b04f-9b3ed78cb087
    2025-07-15 23:25:41,196 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:25:55,241 INFO status has been updated to running
    INFO:ecmwf.datastores.legacy_client:status has been updated to running
    2025-07-15 23:26:14,953 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    92fedc44364dd0cc866ed52264f2b70a.zip:   0%|          | 0.00/1.11M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_prec_bounding_box_2024_chunk1.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_prec_bounding_box_2024_chunk1.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_prec_bounding_box_2024_chunk1/data_stream-oper_stepType-accum.nc[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_prec_bounding_box_2024_chunk1/data_stream-oper_stepType-instant.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 2 file(s)[0m
    [0m  Processing file 1/2: data_stream-oper_stepType-accum.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 336, 'latitude': 41, 'longitude': 41})[0m
    [0m  Processing file 2/2: data_stream-oper_stepType-instant.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 336, 'latitude': 41, 'longitude': 41})[0m
    [0m[0;32m✓ Chunk completed in 37.5 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 2/2[0m
    Date Range: 2024-01-15 to 2024-01-15
    Variables:  2m_temperature, total_precipitation[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:26:27,800 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:26:28,550 INFO Request ID is 208bed7b-944e-4062-8c0c-55fd3cd1979d
    INFO:ecmwf.datastores.legacy_client:Request ID is 208bed7b-944e-4062-8c0c-55fd3cd1979d
    2025-07-15 23:26:28,762 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:27:02,616 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    4727f46fced746f374321037dfb8b83f.zip:   0%|          | 0.00/120k [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_prec_bounding_box_2024_chunk2.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_prec_bounding_box_2024_chunk2.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_prec_bounding_box_2024_chunk2/data_stream-oper_stepType-accum.nc[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/temp_prec_bounding_box_2024_chunk2/data_stream-oper_stepType-instant.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 2 file(s)[0m
    [0m  Processing file 1/2: data_stream-oper_stepType-accum.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 24, 'latitude': 41, 'longitude': 41})[0m
    [0m  Processing file 2/2: data_stream-oper_stepType-instant.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 24, 'latitude': 41, 'longitude': 41})[0m
    [0m[0;32m✓ Chunk completed in 37.4 seconds[0m[0m
    [0m[0;34mAGGREGATING DATA (DAILY)[0m[0m
    [0mAggregating data to daily frequency...[0m
    [0mSum columns: ['tp'][0m
    [0mMax columns: [][0m
    [0mMin columns: [][0m
    [0mRate columns: [][0m
    [0mAverage columns: ['t2m'][0m
    [0mAggregation completed in:   0.11 seconds[0m
    [0m
    Saving files to output directory: temp_prec_bounding_box_2024_output[0m
    [0m  Saved final data to: temp_prec_bounding_box_2024_output/temp_prec_bounding_box_2024_daily_data.csv[0m
    [0m  Saved unique coordinates to: temp_prec_bounding_box_2024_output/temp_prec_bounding_box_2024_unique_latlongs.csv[0m
    [0m  Saved raw data to: temp_prec_bounding_box_2024_output/temp_prec_bounding_box_2024_raw_data.csv[0m
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
    [0mTotal complete processing time: 86.85 seconds[0m
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


You can also request relative humidity at a specific pressure level.


```python
df_bounding_box_pressure = varunayan.era5ify_bbox(
    request_id="bounding_box_pressure_relative_humidity",
    variables=["temperature", "relative_humidity"],
    start_date="2024-01-1",
    end_date="2024-01-15",
    north=30,
    south=20,
    east=80,
    west=70,
    dataset_type="pressure",
    pressure_levels=["1000"],
    frequency="daily",
    resolution=0.25,
)
```

    [0m✓ CDS API configuration is already set up and valid.[0m
    [0m
    ============================================================[0m
    [0m[0;34mSTARTING ERA5 PRESSURE LEVEL PROCESSING[0m[0m
    [0m============================================================[0m
    [0mRequest ID: bounding_box_pressure_relative_humidity[0m
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


    2025-07-15 23:27:07,187 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:27:07,613 INFO Request ID is 667e7488-1b45-4f20-a600-529d6f54b533
    INFO:ecmwf.datastores.legacy_client:Request ID is 667e7488-1b45-4f20-a600-529d6f54b533
    2025-07-15 23:27:07,958 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:27:17,267 INFO status has been updated to running
    INFO:ecmwf.datastores.legacy_client:status has been updated to running
    2025-07-15 23:27:22,556 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    a31c95b4d651ba01a259e57c5425653a.nc:   0%|          | 0.00/1.98M [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/bounding_box_pressure_relative_humidity_chunk1.nc[0m[0m
    [0mCopying NetCDF file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/bounding_box_pressure_relative_humidity_chunk1.nc[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/bounding_box_pressure_relative_humidity_chunk1/bounding_box_pressure_relative_humidity_chunk1.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: bounding_box_pressure_relative_humidity_chunk1.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 336, 'pressure_level': 1, 'latitude': 41, 'longitude': 41})[0m
    [0m[0;32m✓ Chunk completed in 18.8 seconds[0m[0m
    [0m[0;36mPROCESSING CHUNK 2/2[0m
    Date Range: 2024-01-15 to 2024-01-15
    Variables:  temperature, relative_humidity
    Levels:     1000[0m
    [0m  → Downloading ERA5 data (attempt 1/6)...[0m


    2025-07-15 23:27:36,063 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:27:36,736 INFO Request ID is 1ea5967f-d8e7-467f-a986-fbc6821c6a44
    INFO:ecmwf.datastores.legacy_client:Request ID is 1ea5967f-d8e7-467f-a986-fbc6821c6a44
    2025-07-15 23:27:36,998 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:27:46,166 INFO status has been updated to running
    INFO:ecmwf.datastores.legacy_client:status has been updated to running
    2025-07-15 23:27:51,497 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    acb288b5bd9e45b35d8b62e7a8c97725.nc:   0%|          | 0.00/187k [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/bounding_box_pressure_relative_humidity_chunk2.nc[0m[0m
    [0mCopying NetCDF file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/bounding_box_pressure_relative_humidity_chunk2.nc[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/bounding_box_pressure_relative_humidity_chunk2/bounding_box_pressure_relative_humidity_chunk2.nc[0m
    [0m
    Processing downloaded data:[0m
    [0m- Found 1 file(s)[0m
    [0m  Processing file 1/1: bounding_box_pressure_relative_humidity_chunk2.nc[0m
    [0m  ✓ Loaded: Dimensions: Frozen({'valid_time': 24, 'pressure_level': 1, 'latitude': 41, 'longitude': 41})[0m
    [0m[0;32m✓ Chunk completed in 17.9 seconds[0m[0m
    [0m[0;34mAGGREGATING DATA (DAILY)[0m[0m
    [0mAggregating pressure level data to daily frequency...[0m
    [0mVariables to average: ['t', 'r'][0m
    [0mIncluding pressure_level in aggregation groups[0m
    [0mAggregation completed in:   0.05 seconds[0m
    [0m
    Saving files to output directory: bounding_box_pressure_relative_humidity_output[0m
    [0m  Saved final data to: bounding_box_pressure_relative_humidity_output/bounding_box_pressure_relative_humidity_daily_data.csv[0m
    [0m  Saved unique coordinates to: bounding_box_pressure_relative_humidity_output/bounding_box_pressure_relative_humidity_unique_latlongs.csv[0m
    [0m  Saved raw data to: bounding_box_pressure_relative_humidity_output/bounding_box_pressure_relative_humidity_raw_data.csv[0m
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
    [0mTotal complete processing time: 48.61 seconds[0m
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

And finally, you can request weather at a particular latitute and longitude


```python
df = varunayan.era5ify_point(
    request_id="test5",
    variables=["2m_temperature", "total_precipitation"],
    start_date="2024-08-1",
    end_date="2024-08-14",
    latitude=19.1331,
    longitude=72.9151,
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
    [0mGeoJSON File: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/test5_temp_geojson.json[0m
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


    2025-07-15 23:27:55,846 INFO [2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    INFO:ecmwf.datastores.legacy_client:[2024-09-26T00:00:00] Watch our [Forum](https://forum.ecmwf.int/) for Announcements, news and other discussed topics.
    2025-07-15 23:27:56,816 INFO Request ID is c76b92d3-768e-414a-9f69-b1c87166ea22
    INFO:ecmwf.datastores.legacy_client:Request ID is c76b92d3-768e-414a-9f69-b1c87166ea22
    2025-07-15 23:27:57,029 INFO status has been updated to accepted
    INFO:ecmwf.datastores.legacy_client:status has been updated to accepted
    2025-07-15 23:28:05,939 INFO status has been updated to running
    INFO:ecmwf.datastores.legacy_client:status has been updated to running
    2025-07-15 23:28:11,200 INFO status has been updated to successful
    INFO:ecmwf.datastores.legacy_client:status has been updated to successful



    dffcb8e7ff13a873fc3cfbffba3cec65.zip:   0%|          | 0.00/105k [00:00<?, ?B/s]


    [0m  [0;32m✓ Download completed: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/test5.zip[0m[0m
    [0mExtracting zip file: /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/test5.zip[0m
    [0mExtracted NetCDF files:[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/test5/data_stream-oper_stepType-accum.nc[0m
    [0m  - /var/folders/gl/sfjd74gn0wv11h31lr8v2cj40000gn/T/test5/data_stream-oper_stepType-instant.nc[0m
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
    [0m✓ Dataset filtering completed in 0.00 seconds[0m
    [0m
    --- Final Filtering Results ---[0m
    [0mTotal processing time: 0.01 seconds[0m
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
    [0m  Saved final data to: test5_output/test5_daily_data.csv[0m
    [0m  Saved unique coordinates to: test5_output/test5_unique_latlongs.csv[0m
    [0m  Saved raw data to: test5_output/test5_raw_data.csv[0m
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
    [0mTotal complete processing time: 17.74 seconds[0m
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


    

# Searching for variables

Climate science has many variables. Varunayan allows you to search which variables are part of which dataset:



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
    


# Description of variables

A detailed description for each variable is also available using `describe_variables`:


```python
# varunayan.describe_variables(variable_names, dataset_type)
# variable_names : list, list of variable names to describe
# dataset_type : str, type of dataset (single or pressure, for single level or pressure level datasets)
```


```python
varunayan.describe_variables(
    variable_names=["2m_temperature", "total_precipitation", "surface_pressure"],
    dataset_type="single",
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

