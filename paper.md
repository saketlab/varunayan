---
title: 'varunayan: A Python Package for Simplified ERA5 Climate Data Retrieval and Processing'
tags:
    - Python
    - climate data
    - ERA5
    - meteorology
    - geospatial analysis
authors:
    - name: Atharva Jagtap
      orcid: 
      equal-contrib: true
      affiliation: 1
    - name: Saket Choudhary
      orcid: 0000-0001-5202-7633
      equal-contrib: true
      affiliation: 2
affiliations:
    - name: Bharatiya Vidya Bhavan's Sardar Patel Institute of Technology
      index: 1
    - name: Indian Institute of Technology Bombay
      index: 2
date:
bibliography: paper.bib
---

# Summary

Varunayan is an open-source Python package and CLI tool designed to simplify the process of acquiring ERA5 climate data from the Copernicus Climate Data Store [@era5_pressure_hourly; @era5_single_hourly]. It allows users to effortlessly extract climate variables (such as temperature, precipitation, wind, etc.) for custom geographical regions, either defined by GeoJSON files, bounding boxes, or point coordinates. The package automates spatial filtering, temporal aggregation, and provides output in CSV format, making ERA5 data more accessible for research, analysis, and operational workflows. 

# Statement of Need

Climate and environmental researchers increasingly rely on ERA5 reanalysis data for studying weather patterns, validating models, and understanding environmental changes [@era5_pressure_hourly; @era5_single_hourly; @era5_pressure_monthly; @era5_single_monthly]. However, the technical barriers to accessing this data create significant obstacles, particularly for researchers without extensive programming backgrounds or familiarity with geospatial data formats. 
The official Climate Data Store API (cdsapi) provides low-level access but requires users to construct request dictionaries, manually split large temporal ranges to avoid timeouts, write custom code for spatial subsetting, and implement variable-specific aggregation logic. These repetitive tasks are error prone and time consuming, diverting researcher effort from scientific analysis to data engineering.
Varunayan addresses these challenges by providing high-level functions that encapsulate best practices for ERA5 data access. What would normally require hundreds of lines of custom code becomes a single function call that handles the entire workflow from data request to analysis-ready output.
For students and early-career researchers learning climate data analysis, varunayan reduces the learning curve by abstracting technical complexity, while ensuring scientifically appropriate data handling. For experienced researchers, it eliminates repetitive coding for standard data access patterns, enabling rapid prototyping and reproducible workflows. The package includes comprehensive tutorial notebooks demonstrating typical use cases to help users adapt the code to their specific research questions.

# Functional Overview

## Geographic Flexibility

Varunayan supports three methods for defining study regions:

**Bounding box specification** for rectangular regions:
```python
import varunayan

df = varunayan.era5ify_bbox(
    request_id="rectangle_region",
    variables=["2m_temperature", "total_precipitation"],
    start_date="2020-01-01",
    end_date="2020-12-31",
    north=40.0, south=30.0, east=-10.0, west=-11.0,
    frequency="daily"
)
```

**Point extraction** for station-like data:
```python
df = varunayan.era5ify_point(
    request_id="location_study",
    variables=["2m_temperature", "surface_pressure"],
    start_date="2020-01-01",
    end_date="2020-12-31",
    latitude=34.678,
    longitude=87.4326,
    frequency="hourly"
)
```

**GeoJSON polygons** for irregular boundaries (watersheds, administrative regions, ecological zones):
```python
df = varunayan.era5ify_geojson(
    request_id="watershed_analysis",
    variables=["total_precipitation", "mean_evaporation_rate"],
    start_date="2020-01-01",
    end_date="2020-12-31",
    json_file="watershed_boundary.geojson",
    frequency="monthly"
)
```

## Command-Line Interface

For integration with shell scripts and workflows, varunayan provides a full-featured CLI:

```bash
varunayan geojson \
  --request-id "monsoon_study" \
  --variables "2m_temperature,total_precipitation" \
  --start "2020-06-01" --end "2020-09-30" \
  --geojson "study_region.geojson" \
  --freq daily \
  --verbosity 1
```

## Multi-Feature and Multi-Level Support

The package handles GeoJSON files containing multiple features (e.g., multiple administrative regions), processing each feature separately while maintaining feature attribution in the output. This enables comparative regional analyses without writing custom spatial processing code.

```python
df = varunayan.era5ify_geojson(
    request_id="multi_region",
    variables=["total_precipitation", "2m_temperature"],
    start_date="2020-01-01",
    end_date="2020-12-31",
    json_file="multiple_states.geojson",
    dist_features=["state_name"],
    frequency="monthly"
)
```

## Intelligent Temporal Aggregation

The package implements variable-aware temporal aggregation based on physical characteristics:

- **Cumulative variables** (precipitation, snowfall): Summed over time periods
- **Intensive variables** (temperature, pressure): Averaged over time periods
- **Extreme variables**: Maximum and minimum values preserved appropriately
- **Rate variables**: Treated as intensive properties and averaged

This built-in knowledge eliminates a common source of errors in climate data processing.

## Variable Discovery

To assist users unfamiliar with ERA5 variable naming conventions, the package includes search and description utilities:

```python
# Find relevant variables
varunayan.search_variable("precipitation", dataset_type="single")

# Get detailed information
varunayan.describe_variables(
    ["total_precipitation", "2m_temperature"],
    dataset_type="single"
)
```

# Target Audience and Use Cases

Varunayan is designed for:

- Climate scientists studying regional patterns and variability
- Agricultural researchers examining weather impacts
- Environmental scientists investigating climate-ecosystem relationships
- Public health researchers studying climate-disease associations
- Graduate students learning climate data analysis
- Data scientists incorporating climate features into models

The package is particularly valuable for researchers who need to:

- Work with irregular geographic regions (political boundaries, ecological zones)
- Process multi-year datasets efficiently
- Compare climate variables across multiple regions simultaneously
- Generate reproducible climate analyses with minimal code
- Integrate climate data access into automated workflows

# References
