# Varunayan

<p align="center">
  <img src="https://raw.githubusercontent.com/saketlab/varunayan/main/docs/_static/varunayan_logo.png" alt="Varunayan Logo" width="200"/>
</p>

Python package for downloading and processing climate data from ERA5, IMD, HadEX3, and CRU TS. Includes heat stress index calculations (UTCI, WBGT, Heat Index, Humidex) and country-level temperature aggregation.

Also available in R: [varunayanR](https://github.com/saketlab/varunayanR)

## Data sources

| Source | Variables | Resolution | Coverage |
|--------|-----------|------------|----------|
| [ERA5](https://cds.climate.copernicus.eu/) | 100+ (temperature, precipitation, wind, radiation, etc.) | 0.25 deg, hourly to monthly | 1940-present, global |
| [IMD](https://www.imdpune.gov.in/) | Rainfall, Tmax, Tmin | 0.25/1.0 deg, daily | 1901-present, India |
| [HadEX3](https://www.metoffice.gov.uk/hadobs/hadex3/) | 29 ETCCDI climate extremes | 1.25x1.875 deg, annual/monthly | 1901-2018, global |
| [CRU TS v4.07](https://crudata.uea.ac.uk/cru/data/hrg/) | tmp, tmx, tmn, pre, vap, cld, wet, frs, dtr, pet | 0.5 deg, monthly | 1901-2022, land |

## Installation

```bash
pip install varunayan
```

For development:

```bash
pip install -e .
```

## Quick start

### ERA5 (requires CDS account)

```python
import varunayan

# Bounding box query
df = varunayan.era5ify_bbox(
    request_id="mumbai",
    variables=["2m_temperature", "total_precipitation"],
    start_date="2024-01-01", end_date="2024-01-31",
    north=19.2, south=18.9, east=72.9, west=72.8,
    frequency="daily"
)

# Single point
df = varunayan.era5ify_point(
    "shimla", ["2t"], "2024-01-01", "2024-01-07",
    latitude=31.1, longitude=77.2
)
```

### IMD gridded data (no credentials needed)

```python
# Rainfall for a bounding box
rain = varunayan.imd_rainfall_bbox(
    "maharashtra", start_year=2020, end_year=2023,
    north=22, south=16, east=80, west=73,
    resolution=0.25, frequency="monthly"
)

# Temperature with GeoJSON filter
tmax = varunayan.imd_temperature_geojson(
    "karnataka", start_year=2022, end_year=2023,
    geojson_file="karnataka.geojson", var_type="tmax"
)

# IMD station lookup
stations = varunayan.get_imd_stations()
```

### HadEX3 climate extremes

```python
# Hottest-day trend over India
txx = varunayan.hadex3_bbox(
    "TXx", start_year=1951, end_year=2018,
    north=38, south=6, east=98, west=68
)

# All 29 ETCCDI indices
varunayan.list_hadex3_indices()
```

### CRU TS monthly climate grids

```python
# Mean temperature for a bounding box
tmp = varunayan.cru_ts_bbox(
    "tmp", start_year=2000, end_year=2020,
    north=38, south=6, east=98, west=68
)

# All 10 variables with ERA5/HadEX3 equivalents
varunayan.list_cru_ts_variables()
```

### Country-level temperature

```python
# Cosine-latitude weighted national average
df = varunayan.get_era5_country_temperature(
    "India", "2000-01-01", "2023-12-31",
    variables=["mean", "max", "min"]
)
```

### Heat stress indices

```python
# Individual indices
utci = varunayan.utci(temp_c=35, rh=60, wind_ms=2, mrt_c=50)
hi = varunayan.heat_index(temp_c=35, rh=60)
wbgt = varunayan.wbgt_simple(temp_c=35, dewpoint_c=25)

# All indices at once
indices = varunayan.calc_heat_indices(temp_c=35, dewpoint_c=25, wind_ms=2)

# UTCI sparse Legendre polynomial (Roman et al. 2025, wider wind range)
utci_s = varunayan.utci_sparse(temp_c=35, tmrt=50, wind_speed=2, rh=60)

# Risk categories
varunayan.heat_index_risk_category(hi)
varunayan.utci_category(utci)
```

## CLI

```bash
varunayan bbox --request-id "test" --variables "temperature,relative_humidity" \
  --start "2024-01-01" --end "2024-01-15" \
  --north 30 --south 20 --east 80 --west 70 \
  --dataset-type pressure --pressure-levels "1000,900" \
  --freq daily --res 0.25
```

Also supports `varunayan geojson` and `varunayan point` subcommands.

## Documentation

[varunayan.saketlab.org](https://varunayan.saketlab.org)

## Contributing

Contributions welcome via pull request.

## License

MIT License. See [LICENSE](LICENSE).
