# Eranest

A Python package for downloading and processing ERA5 climate data.

## Installation

You can install Eranest using pip:

```bash
pip install eranest
```

## Quick Start

(refer eranest demo notebook, snippet is to be added here)

Quickly download ERA5 reanalysis data using the command line:
1. either by providing a GeoJSON file to define the area of interest
```bash
eranest geojson --request-id "request_name" --variables "var1,var2,etc." --start "yyyy-mm-dd" --end "yyyy-mm-dd" --geojson "your_file.geojson" --freq "hourly" --res 0.25
```
2. or by providing a bounding box to define the area of interest
```bash
eranest bbox --request-id "request_name" --variables "var1,var2,etc." --start "yyyy-mm-dd" --end "yyyy-mm-dd" --north 45.0 --south 40.0 --east -45.0 --west -40.0 --freq "hourly" --res 0.25
```

## Features

- Download ERA5 climate data for any custom geographical area
- Process and analyze climate data
- Support for various climate variables
- ...

## Documentation

For detailed documentation, please visit our [documentation page](docs/).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
