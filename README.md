# Varunayan

<p align="center">
  <img src="https://raw.githubusercontent.com/saketlab/varunayan/main/docs/_static/varunayan_logo.png" alt="Varunayan Logo" width="200"/>
</p>

A Python package for downloading and processing ERA5 climate data.

## Installation

Install the latest release from PyPI:

```bash
pip install varunayan
```

For development, clone the repository and install it locally:

```bash
pip install -e .
```

## Quick Start


Quickly extract ERA5 processed data with the help of *varunayan* from the command line:


1. either by providing a GeoJSON file to define the area of interest
```bash
varunayan geojson --request-id "request_name" --variables "var1,var2,etc." --start "yyyy-mm-dd" --end "yyyy-mm-dd" --geojson "your_file.geojson" --dataset-type "dataset_type" --pressure-levels "pressure_level_1,pressure_level_2,etc." --freq "frequency" --res "resolution"
```

2. or by providing a bounding box to define the area of interest
```bash
varunayan bbox --request-id "request_name" --variables "var1,var2,etc." --start "yyyy-mm-dd" --end "yyyy-mm-dd" --north "north_bound" --south "south_bound" --east "east_bound" --west "west_bound" --dataset-type "dataset_type" --pressure-levels "pressure_level_1,pressure_level_2,etc." --freq "frequency" --res "resolution"
```

3. or by providing coordinates of the location
```bash
varunayan point --request-id "request_name" --variables "var1,var2,etc." --start "yyyy-mm-dd" --end "yyyy-mm-dd" --lat "latitude" --lon "longitude" --dataset-type "dataset_type" --pressure-levels "pressure_level_1,pressure_level_2,etc." --freq "frequency"
```

The arguments dataset-type (single by default), pressure-levels (empty by default), freq (hourly by default) and res (0.25 by default) are optional.

Example command for extracting pressure-level data for a bounding box
```bash
varunayan bbox --request-id "test" --variables "temperature,relative_humidity" --start "2024-01-1" --end "2024-01-15" --north 30 --south 20 --east 80 --west 70 --dataset-type pressure --pressure-levels "1000,900" --freq daily --res 0.25
```

## Documentation

Please visit our [documentation page](http://saketlab.github.io/varunayan) for detailed documentation.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 


