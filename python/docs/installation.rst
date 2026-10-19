Installation
============

Requirements
------------

varunayan needs Python 3.10 or higher. pip installs these packages with it:
cdsapi, xarray, netCDF4, numpy, pandas, geopandas, shapely,
python-dateutil, requests, matplotlib and tqdm.

Install from PyPI
-----------------

.. code-block:: bash

   pip install varunayan

CDS API Setup
-------------

varunayan uses the Copernicus Climate Data Store (CDS) API to download ERA5
data. IMD, HadEX3 and CRU TS data do not need an account.

1. Create a free account at https://cds.climate.copernicus.eu/.
2. Accept the ERA5 licence on the CDS website.
3. Copy your API token from https://cds.climate.copernicus.eu/profile.
4. Give the token to varunayan in one of these ways:

   - Set the ``CDS_API_KEY`` (or ``CDSAPI_KEY``) environment variable.
     varunayan then writes ``~/.cdsapirc`` for you.
   - Write ``~/.cdsapirc`` yourself:

     .. code-block:: bash

        echo "url: https://cds.climate.copernicus.eu/api" > ~/.cdsapirc
        echo "key: YOUR_API_KEY" >> ~/.cdsapirc

   - Do nothing. On the first import, varunayan asks for the token.

Development Installation
------------------------

Install the latest version from GitHub:

.. code-block:: bash

   pip install "git+https://github.com/saketlab/varunayan.git#subdirectory=python"

To contribute to varunayan:

.. code-block:: bash

   git clone https://github.com/saketlab/varunayan.git
   cd varunayan/python
   pip install -e ".[dev]"

The ``dev`` extra installs pytest, black, isort, flake8 and mypy.

Verification
------------

.. code-block:: python

   import varunayan
   print(varunayan.__version__)

Test the command line interface:

.. code-block:: bash

   varunayan --help
