# Changelog


```{admonition} Version Information
:class: info

You are viewing the changelog for **version {doc}`/index`**. 
Use the version selector in the sidebar to view changes for different versions.
```

## [Unreleased] - YYYY-MM-DD

### Added
- Initial release of Varunayan Python package
- **Core Processing Functions**:
  - `era5ify_geojson()`: Process climate data using GeoJSON files
  - `era5ify_bbox()`: Process data using bounding box coordinates  
  - `era5ify_point()`: Process data using single point coordinates
- **Command-Line Interface** with three processing modes:
  - `varunayan geojson`: Process using GeoJSON/JSON files
  - `varunayan bbox`: Process using bounding box coordinates
  - `varunayan point`: Process using single point (lat, lon)
- **ERA5 Data Integration**:
  - Automatic download from Climate Data Store (CDS) API
  - Support for both single-level and pressure-level variables
  - Retry logic with exponential backoff for failed downloads
  - CDS API configuration validation
- **Advanced Processing Features**:
  - Automatic time-based chunking for large requests (>14 days or >100 months)
  - NetCDF processing with spatial filtering
  - Temporal aggregation by frequency (daily, monthly, yearly)
  - Smart handling of sum variables (precipitation, radiation) during aggregation


---

**Links**: 
- [PyPI Package](https://pypi.org/project/varunayan/) (not yet released)
- [GitHub Repository](https://github.com/saketlab/varunayan)
- [Documentation](https://saketlab.github.io/varunayan/)
- [Issue Tracker](https://github.com/saketlab/varunayan/issues)

[Unreleased]: https://github.com/saketlab/varunayan/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/saketlab/varunayan/releases/tag/v0.1.0
