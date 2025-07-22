# Installation

```{admonition} Prerequisites
:class: note

- **Python 3.8+** - Varunayan supports Python 3.8 and higher
- **CDS API Token** - Registration required (free)
```

## Quick Install

### Basic Installation
```bash
pip install varunayan
```

### With Documentation Tools
```bash
pip install varunayan[docs-build]
```

### For Development
```bash
pip install varunayan[dev,quality,test]
```

## Installation Options

### End Users

::::{grid} 1 2 2 2
:::{grid-item-card} Basic Package
:class-card: text-center

```bash
pip install varunayan
```

Core functionality only
:::

:::{grid-item-card} With Notebook Support
:class-card: text-center

```bash
pip install varunayan[docs-build]
```

Includes Jupyter notebook tools
:::
::::

### Developers & Contributors

::::{grid} 1 2 2 2
:::{grid-item-card} Development
:class-card: text-center

```bash
pip install varunayan[dev,quality,test]
```

Testing, linting, type checking
:::

:::{grid-item-card} Documentation
:class-card: text-center

```bash
pip install varunayan[docs,docs-serve]
```

Full documentation tools
:::

:::{grid-item-card} Building
:class-card: text-center

```bash
pip install varunayan[build]
```

Package building tools
:::

:::{grid-item-card} Everything
:class-card: text-center

```bash
pip install varunayan[all]
```

All optional dependencies
:::
::::

## Development Installation

For development work, clone the repository and install in editable mode:

```bash
git clone https://github.com/saketlab/varunayan.git
cd varunayan
pip install -e .[dev,quality,test]
```

This includes:
- **Testing**: pytest, pytest-cov, pytest-xdist
- **Code Quality**: black, isort, flake8, mypy
- **Security**: bandit, safety
- **Pre-commit hooks**: Automated code quality checks

## CDS API Setup

```{admonition} Required for Data Download
:class: warning

Varunayan requires access to the Copernicus Climate Data Store (CDS) API to download ERA5 data.
```

### Step 1: Register for CDS Access

1. Go to [CDS Website](https://cds.climate.copernicus.eu/)
2. Create a free account

### Step 2: Get Your API Token

1. Log in to [CDS](https://cds.climate.copernicus.eu/)
2. Go to your [Profile](https://cds.climate.copernicus.eu/profile)
3. Copy your API Token

### Step 3: Configure API Access

`varunayan` will automatically handle the API configuration. No need to manually create or edit the `.cdsapirc` file! Just run the package and provide your API token when prompted.

```{admonition} Security Note
:class: tip

The API token you provide is **only used to generate the `.cdsapirc` file** for configuring access to the CDS API.  
`varunayan` does **not store, transmit, or use your token for anything else.**
```

## Verify Installation

Test that everything is working correctly:

### Command Line
```bash
# Check version
varunayan --help

# Test CLI functionality  
varunayan --version
```

### Python
```python
# Test import
import varunayan
print(f"Varunayan version: {varunayan.__version__}")

# Test function availability
print("Available functions:")
for func in ['era5ify_geojson', 'era5ify_bbox', 'era5ify_point']:
    if hasattr(varunayan, func):
        print(f"  ✓ {func}")
    else:
        print(f"  ✗ {func}")
```

## Troubleshooting

```{admonition} Common Issues
:class: warning

**Import errors**: Install missing dependencies with `pip install varunayan[all]`

**CDS API errors**: Check your `~/.cdsapirc` file and credentials

**Permission errors**: Use `--user` flag: `pip install --user varunayan`

**Version conflicts**: Create a virtual environment:

    python -m venv varunayan-env
    source varunayan-env/bin/activate  # On Windows: varunayan-env\Scripts\activate
    pip install varunayan
```

## Next Steps

Once installed, check out:

- [Usage Guide](usage.md) - Learn the basics
- [Tutorials](tutorials/index.md) - Step-by-step examples  
- [API Reference](api_reference/index.md) - Complete documentation

---

*Need help? [Open an issue](https://github.com/saketlab/varunayan/issues) on GitHub!*