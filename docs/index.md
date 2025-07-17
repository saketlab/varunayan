# Welcome to Varunayan's Documentation!

```{admonition} What is Varunayan?
:class: tip

Varunayan is a powerful Python package for downloading and processing **ERA5 climate data**. 
It provides both command-line and Python APIs for extracting analysis-ready climate data 
for custom geographical regions using GeoJSON files, bounding boxes, or point coordinates.
```

## Key Features

::::{grid} 1 2 2 3
:::{grid-item-card} Multiple Input Formats
:class-card: text-center

Support for GeoJSON files, bounding boxes, and point coordinates
:::

:::{grid-item-card} Flexible Processing
:class-card: text-center

Hourly, daily, weekly, monthly, and yearly aggregations
:::

:::{grid-item-card} Efficient Downloads
:class-card: text-center

Automatic chunking for large requests with retry logic
:::

:::{grid-item-card} Comprehensive Output
:class-card: text-center

CSV files with raw data, aggregated data, and coordinates
:::

:::{grid-item-card} Dual APIs
:class-card: text-center

Command-line interface and Python API
:::

:::{grid-item-card} Variable Discovery
:class-card: text-center

Search and describe ERA5 variables easily
:::
::::

## Quick Start

### Installation
```bash
pip install varunayan
```

### Usage Examples

````{tab-set}
```{tab-item} Python API

```python
import varunayan

# Download temperature data for a region
df = varunayan.era5ify_geojson(
    request_id="my_analysis",
    variables=["2m_temperature", "total_precipitation"],
    start_date="2023-01-01",
    end_date="2023-01-31",
    json_file="region.geojson",
    frequency="daily"
)
```

```{tab-item} Command Line

```bash
varunayan geojson \
    --request-id "my_analysis" \
    --variables "2m_temperature,total_precipitation" \
    --start-date "2023-01-01" \
    --end-date "2023-01-31" \
    --json-file "region.geojson" \
    --frequency "daily"
```
````

```{admonition} Need Help?
:class: note

- Check out our [tutorials](tutorials/index.md) for detailed examples
- Browse the [API reference](api_reference/index.md) for complete documentation
- Report issues on [GitHub](https://github.com/saketlab/varunayan/issues)
```

## Documentation Contents

```{toctree}
:maxdepth: 2
:caption: Getting Started

installation
usage
```

```{toctree}
:maxdepth: 2
:caption: Tutorials & Examples

tutorials/index
tutorials/eranest_demo
tutorials/eranest_India_temp_change
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api_reference/index
autoapi/index
```

```{toctree}
:maxdepth: 1
:caption: Development

DEPENDENCIES
```

## Search & Navigate

Use the search bar above or press `Ctrl+K` (or `⌘K` on Mac) to quickly find what you're looking for.

**Keyboard shortcuts:**
- `Ctrl+K` / `⌘K`: Open search
- `Alt+←/→`: Navigate between pages
- `s`: Toggle sidebar
- `t`: Go to top

## Contributing

We welcome contributions! Please see our [GitHub repository](https://github.com/saketlab/varunayan) for:

- Bug reports
- Feature requests  
- Documentation improvements
- Code contributions

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/saketlab/varunayan/blob/main/LICENSE) file for details.

---

*Built by the Varunayan team*