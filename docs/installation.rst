Installation
============

Requirements
------------

varunayan requires Python 3.9 or higher and the following packages:

- requests>=2.25.0
- pandas>=1.3.0
- xarray>=0.18.0
- netCDF4>=1.5.0
- cdsapi>=0.5.0
- geopandas>=0.10.0 (optional, for GeoJSON support)
- shapely>=1.7.0 (optional, for spatial operations)

Install from PyPI
-----------------

The recommended way to install varunayan is via pip:

.. code-block:: bash

   pip install varunayan

CDS API Setup
-------------

varunayan uses the Copernicus Climate Data Store (CDS) API to download ERA5 data. You need to:

1. Create a free account at https://cds.climate.copernicus.eu/
2. Install the CDS API key by creating a ``.cdsapirc`` file in your home directory:

.. code-block:: bash

   # Create the configuration file
   echo "url: https://cds.climate.copernicus.eu/api/v2" > ~/.cdsapirc
   echo "key: YOUR_API_KEY" >> ~/.cdsapirc

Replace ``YOUR_API_KEY`` with your actual API key from the CDS website.

Development Installation
------------------------

Install the latest development version from GitHub:

.. code-block:: bash

   pip install git+https://github.com/saketlab/varunayan.git

Or if you want to contribute to varunayan:

.. code-block:: bash

   git clone https://github.com/saketlab/varunayan.git
   cd varunayan
   pip install -e ".[dev]"

This will install varunayan in development mode with all development dependencies including:

- pytest (for testing)
- black (for code formatting)
- flake8 (for linting)
- mypy (for type checking)
- isort (for import sorting)

Verification
------------

To verify your installation, run:

.. code-block:: python

   import varunayan
   print(varunayan.__version__)

Or test the command line interface:

.. code-block:: bash

   varunayan --help

Test your CDS API configuration:

.. code-block:: python

   import cdsapi
   
   # This should work without errors if CDS API is properly configured
   c = cdsapi.Client()
   print("CDS API configured successfully!")