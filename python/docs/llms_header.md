# varunayan

> Python package to download and process climate reanalysis and observational data. It has a focus on India, but it supports global datasets. An R package with the same functions and output is at https://varunayan.saketlab.org/R/.

varunayan gets data from ERA5 reanalysis, IMD gridded observations, HadEX3 climate extremes indices and CRU TS monthly climate grids. It also has heat stress indices (UTCI, WBGT, Heat Index, Humidex), country-level temperature, analysis and plot functions, ERA5 variable search, spatial aggregation and a download cache.

## Data Sources

- ERA5: global reanalysis from ECMWF/Copernicus CDS. 0.25 degree grid, hourly, 1940 to present. Single-level and pressure-level datasets. Regions: bounding box, point or GeoJSON polygon.
- IMD: India Meteorological Department gridded data. Rainfall at 0.25 degree (NetCDF), temperature (tmax, tmin, tmean) at 1 degree (binary .grd), 1901 to present.
- HadEX3: Hadley Centre global ETCCDI climate extremes indices. 1.25 x 1.875 degree grid, 1901 to 2018. Annual and monthly frequencies.
- CRU TS v4.07: Climatic Research Unit monthly climate grids. 0.5 degree, 1901 to 2022, land only. Variables: tmp, tmx, tmn, dtr, pre, wet, frs, vap, cld, pet.

## Installation

```
pip install varunayan
```

Requires Python 3.10+. ERA5 downloads need a CDS API key. Set CDS_API_KEY (or CDSAPI_KEY), write ~/.cdsapirc, or enter the key when varunayan asks for it.

## ERA5 usage

```python
from varunayan import era5ify_bbox, era5ify_point, era5ify_geojson, spatial_mean

df = era5ify_bbox(request_id="demo", variables=["2m_temperature"], start_date="2023-06-01", end_date="2023-06-30", north=28.7, south=28.5, east=77.3, west=77.0, frequency="daily")
df = era5ify_point(request_id="point", variables=["2m_temperature"], start_date="2023-06-01", end_date="2023-06-30", lat=28.6, lon=77.2)
df = era5ify_geojson(request_id="geo", variables=["2m_temperature"], start_date="2023-06-01", end_date="2023-06-30", json_file="region.geojson", level="feature")

# Regional mean, weighted by cos(latitude)
daily = spatial_mean(df, "value", by=["variable", "datetime"])
```

Output: a long DataFrame with columns `datetime`, `latitude`, `longitude`, `pressure_level` (pressure-level data only), `variable` (ERA5 short name, for example `t2m`, `tp`) and `value`. Monthly data also has `year` and `month`; yearly data has `year`. With `convert_units=True` (default), temperatures are in Celsius and precipitation is in mm. Accumulated variables are totals for monthly and yearly data.

`era5ify_point` returns the grid cell nearest to (lat, lon). `era5ify_geojson(level="union")` (default) returns each grid cell inside the union of the features; `level="feature"` returns one row for each feature, with the mean of its cells and the feature properties in place of latitude and longitude.

Common parameters: `dataset_type` ("single" or "pressure"), `pressure_levels` (list of strings, for example ["1000", "850"]), `frequency` ("hourly", "daily", "weekly", "monthly", "yearly"; default "hourly"), `resolution` (degrees, default 0.25; not for era5ify_point), `verbosity` (0, 1, 2), `save_raw` (default False), `convert_units` (default True).

Files: each request writes `{request_id}_output/{request_id}_{frequency}_data.csv` (the long table) and `{request_id}_unique_latlongs.csv`, plus `{request_id}_raw_data.csv` when save_raw=True.

## Command line

The CLI gets ERA5 data with three subcommands: `geojson`, `bbox` and `point`.

```
varunayan bbox --request-id demo --variables 2m_temperature --start 2023-06-01 --end 2023-06-30 --north 28.7 --south 28.5 --east 77.3 --west 77.0
varunayan point --request-id pt --variables 2m_temperature --start 2023-06-01 --end 2023-06-01 --lat 28.6 --lon 77.2
varunayan geojson --request-id geo --variables 2m_temperature --start 2023-06-01 --end 2023-06-30 --geojson region.geojson --level feature
```

Common flags: `--dataset-type` (single|pressure), `--pressure-levels` (comma-separated), `--freq` (hourly|daily|weekly|monthly|yearly), `--res` (grid resolution in degrees), `--verbosity` (0|1|2), `--save-raw` (True|False; default False). GeoJSON flag: `--level` (union|feature).

IMD, HadEX3 and CRU TS do not have CLI subcommands. Use the Python API.

## Links

- Docs: https://varunayan.saketlab.org/python/
- R package docs: https://varunayan.saketlab.org/R/
- GitHub: https://github.com/saketlab/varunayan
- PyPI: https://pypi.org/project/varunayan/
