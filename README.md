# Eranest

A Python package for downloading and processing ERA5 climate data.

## Installation

You can install Eranest using pip:

```bash
pip install eranest
```

## Quick Start

(refer eranest demo notebook, snippet is to be added here)

Quickly extract ERA5 processed data with the help of *eranest* from the command line:
1. either by providing a GeoJSON file to define the area of interest
```bash
eranest geojson --request-id "request_name" --variables "var1,var2,etc." --start "yyyy-mm-dd" --end "yyyy-mm-dd" --geojson "your_file.geojson" --dataset-type "dataset_type" --pressure-levels "pressure_level_1,pressure_level_2,etc." --freq "frequency" --res "resolution"
```
2. or by providing a bounding box to define the area of interest
```bash
eranest bbox --request-id "request_name" --variables "var1,var2,etc." --start "yyyy-mm-dd" --end "yyyy-mm-dd" --north "north_bound" --south "south_bound" --east "east_bound" --west "west_bound" --dataset-type "dataset_type" --pressure-levels "pressure_level_1,pressure_level_2,etc." --freq "frequency" --res "resolution"
```
3. or by providing coordinates of the location
```bash
eranest point --request-id "request_name" --variables "var1,var2,etc." --start "yyyy-mm-dd" --end "yyyy-mm-dd" --lat "latitude" --lon "longitude" --dataset-type "dataset_type" --pressure-levels "pressure_level_1,pressure_level_2,etc." --freq "frequency"
```
The arguments dataset-type (single by default), pressure-levels (empty by default), freq (hourly by default) and res (0.25 by default) are optional.

Example command for extracting pressure-level data for a bounding box
```bash
eranest bbox --request-id "test" --variables "temperature,relative_humidity" --start "2024-01-1" --end "2024-01-15" --north 30 --south 20 --east 80 --west 70 --dataset-type pressure --pressure-levels "1000,900" --freq daily --res 0.25
```

## Features

- Acquire ERA5 climate data for any custom geographical area
- Extract ready-to-analyze climate data
- Support for various climate variables
- ...

## Documentation

For detailed documentation, please visit our [documentation page](docs/).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
