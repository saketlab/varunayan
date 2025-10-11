Jupyter Notebooks
=================

This directory contains interactive Jupyter notebooks demonstrating various use cases and features of varunayan.

Available Notebooks
-------------------

1. **Getting Started** (:doc:`01_quickstart`)
   
   Introduction to varunayan's basic functionality and core concepts.

2. **ERA5 vs IMD Comparison** (:doc:`02_era5_imd_comparison`)
   
   Comparing ERA5 reanalysis data with Indian Meteorological Department observations.

3. **Temperature Change Analysis** (:doc:`03_temperature_change_india`)
   
   Analyzing long-term temperature trends across India using ERA5 data.

4. **Weather-dependent Sales Analysis** (:doc:`04_umbrella_sales_India`)
   
   Correlating umbrella sales with precipitation patterns in India.

5. **Regional Climate Analysis** (:doc:`05_sunscreen_sales_California`)
   
   Analyzing UV radiation and temperature patterns in California.

6. **Public Health Applications** (:doc:`06_malaria_dengue_public_interest_trend`)
   
   Exploring relationships between climate variables and disease patterns.

7. **Seasonal Patterns** (:doc:`07_rainfall_peak_India`)
   
   Identifying rainfall peaks and monsoon patterns across Indian regions.

8. **Comparative Analysis** (:doc:`08_era5_imd_temp_comparison`)
   
   Detailed temperature comparison between ERA5 and IMD datasets.

Running the Notebooks
----------------------

Prerequisites
~~~~~~~~~~~~~

Before running the notebooks, ensure you have:

1. **varunayan installed** with notebook dependencies:

   .. code-block:: bash
   
      pip install varunayan[notebooks]

2. **CDS API configured** with your Copernicus Climate Data Store credentials:

   .. code-block:: bash
   
      # Create ~/.cdsapirc with your API key
      echo "url: https://cds.climate.copernicus.eu/api/v2" > ~/.cdsapirc
      echo "key: YOUR_API_KEY" >> ~/.cdsapirc

3. **Jupyter** installed:

   .. code-block:: bash
   
      pip install jupyter

Local Execution
~~~~~~~~~~~~~~~

To run the notebooks locally:

.. code-block:: bash

   # Navigate to the notebooks directory
   cd docs/notebooks
   
   # Start Jupyter
   jupyter notebook

Then open any ``.ipynb`` file in your browser.

Online Viewing
~~~~~~~~~~~~~~

You can also view the notebooks online without running them:

- **GitHub**: View static versions on the `varunayan GitHub repository <https://github.com/saketlab/varunayan/tree/main/docs/tutorials>`_
- **Documentation**: Pre-rendered versions are available in this documentation

Common Issues
-------------

Data Download Timeouts
~~~~~~~~~~~~~~~~~~~~~~

If you encounter timeouts when downloading large datasets:

- Reduce the temporal range of your requests
- Use lower spatial resolution (higher ``resolution`` parameter values)
- Process data in smaller chunks

CDS API Errors
~~~~~~~~~~~~~~

Common CDS API issues:

- **Invalid API key**: Check your ``~/.cdsapirc`` configuration
- **Rate limiting**: Wait between large requests
- **Service unavailable**: CDS maintenance periods

Memory Issues
~~~~~~~~~~~~~

For large datasets:

- Use chunked processing (automatically handled by varunayan)
- Increase available RAM
- Process data in smaller geographical regions

Getting Help
------------

If you encounter issues with the notebooks:

1. Check the `GitHub Issues <https://github.com/saketlab/varunayan/issues>`_ page
2. Create a new issue with:
   
   - Notebook name and cell number
   - Complete error message
   - Your system information (OS, Python version, varunayan version)

Contributing Notebooks
-----------------------

We welcome contributions of new notebooks! See our :doc:`../contributing` guide for details on:

- Notebook structure and style guidelines
- Documentation requirements
- Submission process

When contributing notebooks:

- Include clear explanations and motivation
- Use realistic but manageable dataset sizes
- Provide expected outputs and runtime estimates
- Test thoroughly before submission