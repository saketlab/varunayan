# Usage

This guide covers how to use Varunayan for downloading and processing ERA5 climate data.

## Command Line Interface

Varunayan provides a command-line interface with three main modes:

### GeoJSON Mode
Download data for regions defined by GeoJSON files:

```bash
varunayan geojson \
    --request-id "my_analysis" \
    --variables "2m_temperature,total_precipitation" \
    --start-date "2023-01-01" \
    --end-date "2023-01-31" \
    --json-file "region.geojson" \
    --frequency "daily"
```

### Bounding Box Mode
Download data for rectangular regions:

```bash
varunayan bbox \
    --request-id "bbox_analysis" \
    --variables "2m_temperature" \
    --start-date "2023-01-01" \
    --end-date "2023-01-31" \
    --north 40.0 \
    --south 35.0 \
    --east -70.0 \
    --west -80.0 \
    --frequency "daily"
```

### Point Mode
Download data for specific coordinates:

```bash
varunayan point \
    --request-id "point_analysis" \
    --variables "2m_temperature" \
    --start-date "2023-01-01" \
    --end-date "2023-01-31" \
    --latitude 40.7128 \
    --longitude -74.0060 \
    --frequency "daily"
```

## Python API

### GeoJSON Processing
```python
import varunayan

# Download data for a GeoJSON region
df = varunayan.era5ify_geojson(
    request_id="my_analysis",
    variables=["2m_temperature", "total_precipitation"],
    start_date="2023-01-01",
    end_date="2023-01-31",
    json_file="region.geojson",
    frequency="daily"
)
```

### Bounding Box Analysis
```python
# Download data for a bounding box
df = varunayan.era5ify_bbox(
    request_id="bbox_analysis",
    variables=["2m_temperature"],
    start_date="2023-01-01",
    end_date="2023-01-31",
    north=40.0,
    south=35.0,
    east=-70.0,
    west=-80.0,
    frequency="daily"
)
```

### Point Analysis
```python
# Download data for a specific point
df = varunayan.era5ify_point(
    request_id="point_analysis",
    variables=["2m_temperature"],
    start_date="2023-01-01",
    end_date="2023-01-31",
    latitude=40.7128,
    longitude=-74.0060,
    frequency="daily"
)
```

## Variable Search and Description

### Search Variables
```python
# Search for temperature-related variables
results = varunayan.search_variable("temperature", dataset_type="single")
```

### Describe Variables
```python
# Get detailed descriptions
descriptions = varunayan.describe_variables(
    variable_names=["2m_temperature", "total_precipitation"],
    dataset_type="single"
)
```

## Parameters

### Common Parameters
- **`request_id`**: Unique identifier for the request
- **`variables`**: List of ERA5 variables to download
- **`start_date`**: Start date (YYYY-MM-DD format)
- **`end_date`**: End date (YYYY-MM-DD format)
- **`frequency`**: Temporal aggregation (hourly, daily, weekly, monthly, yearly)
- **`dataset_type`**: Data type (single, pressure)
- **`pressure_levels`**: Pressure levels for pressure-level data
- **`resolution`**: Spatial resolution in degrees (default: 0.25)

### Mode-Specific Parameters
- **GeoJSON Mode**: `json_file` - Path to GeoJSON file
- **Bounding Box Mode**: `north`, `south`, `east`, `west` - Coordinates
- **Point Mode**: `latitude`, `longitude` - Point coordinates

## Output Files

Each request generates three CSV files in a `{request_id}_output/` directory:

1. **`{request_id}_{frequency}_data.csv`** - Aggregated data
2. **`{request_id}_unique_latlongs.csv`** - Unique coordinate pairs
3. **`{request_id}_raw_data.csv`** - Raw downloaded data

## Examples

See the [tutorials](tutorials/index.md) for complete examples with real data and visualizations.