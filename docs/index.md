# Welcome to Varunayan's Documentation!

```{admonition} What is Varunayan?
:class: tip

**Varunayan =  Varun + ayan**
- **Varun** in the vedic mythology was the god of sky, order, truth, water and magic. 
- **Ayan** means path in Sanskrit.
**Varunayan**: A smooth path to access clean climate data

---

**Varunayan** is a Python package for downloading and processing **ERA5 climate data**. 
It provides both **command-line** and **Python APIs** for extracting analysis-ready climate data 
for custom geographical regions using:
- GeoJSON files
- Bounding boxes 
- Point coordinates

> Stop spending hours on data wrangling. Focus on your research — Varunayan takes care of the climate data.
```


## Quick Start

### Installation
```bash
pip install git+https://github.com/saketlab/varunayan
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


## Contributing

We welcome contributions! Please see our [GitHub repository](https://github.com/saketlab/varunayan) for:

- Bug reports
- Feature requests  
- Documentation improvements
- Code contributions

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/saketlab/varunayan/blob/main/LICENSE) file for details.

---

