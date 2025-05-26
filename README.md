# Eranest

A Python package for downloading and processing ERA5 climate data.

## Installation

You can install Eranest using pip:

```bash
pip install eranest
```

## Quick Start

```python
from eranest import ERA5Downloader

# Initialize the downloader
downloader = ERA5Downloader()

# Download data for a specific region
data = downloader.download(
    variable='2m_temperature',
    start_date='2020-01-01',
    end_date='2020-01-31',
    region='india'
)
```

## Features

- Download ERA5 climate data for specific regions
- Process and analyze climate data
- Support for various climate variables
- Easy-to-use API

## Documentation

For detailed documentation, please visit our [documentation page](docs/).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 