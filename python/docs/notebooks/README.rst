Jupyter Notebooks
=================

These notebooks show how to use varunayan for real analyses.

Available Notebooks
-------------------

1. :doc:`01_quickstart`: Download ERA5 data for a bounding box, a GeoJSON region,
   a point and pressure levels. Find variables.
2. :doc:`02_climate_of_india`: See the temperature trend, the monsoon peak month,
   climate extremes (HadEX3) and how India compares with other countries.
3. :doc:`03_comparing_datasets`: Compare ERA5 with IMD (rainfall and temperature)
   and with CRU TS, and see when to use each dataset.
4. :doc:`04_spatial_aggregation`: Compare two methods to aggregate grid data to
   districts.
5. :doc:`05_heat_stress`: Calculate and compare the heat stress indices.
6. :doc:`06_public_interest`: Compare rainfall and temperature with Google Trends
   search interest.

The R package has the same six tutorials, with the same function calls.

Running the Notebooks
---------------------

1. Install varunayan with the notebook dependencies:

   .. code-block:: bash

      pip install "varunayan[notebooks]" jupyter

2. Set up the CDS API key (see :doc:`../installation`).

3. Start Jupyter in the notebooks directory:

   .. code-block:: bash

      cd python/notebooks
      jupyter notebook

You can also see the notebooks on
`GitHub <https://github.com/saketlab/varunayan/tree/develop/python/notebooks>`_.

Common Issues
-------------

- **Download timeouts**: Use a shorter time range or a smaller region.
- **CDS API errors**: Check the key in ``~/.cdsapirc``, accept the dataset
  licence on the CDS website, and wait if the CDS is busy or in maintenance.
- **Memory**: Use a smaller region or a coarser ``resolution``. varunayan
  already splits long requests into smaller parts.

Getting Help
------------

Open an issue on `GitHub <https://github.com/saketlab/varunayan/issues>`_.
Include the notebook name, the cell number, the full error message, and your
OS, Python and varunayan versions. See :doc:`../contributing` to add a
notebook.
