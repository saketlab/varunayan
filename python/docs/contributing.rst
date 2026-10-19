Contributing
============

We welcome bug reports, feature requests, code, documentation and notebooks.
Use GitHub Issues for reports and requests, and pull requests for changes.

Development Setup
-----------------

You need Python 3.10 or higher, Git and a GitHub account.

The repository holds the Python package in ``python/`` and the R package in
``R/``.

.. code-block:: bash

   git clone https://github.com/your-username/varunayan.git
   cd varunayan/python
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   pre-commit install

Code Quality
------------

CI runs these checks. Run them before you open a pull request:

.. code-block:: bash

   black varunayan tests && isort varunayan tests   # format (line length 88)
   flake8 varunayan tests                           # lint
   mypy varunayan/                                  # type check

mypy is strict: all functions must have full type hints.

Tests
-----

Tests are in ``tests/`` and use pytest. Shared fixtures are in
``tests/conftest.py``.

.. code-block:: bash

   pytest                              # all tests, with coverage
   pytest tests/test_core.py           # one file
   pytest --no-cov -k heat             # faster, filtered

Tests must not use the network or CDS credentials. Mock ``cdsapi.Client``:

.. code-block:: python

   from unittest.mock import patch

   @patch("varunayan.download.era5_downloader.cdsapi.Client")
   def test_download(mock_client, temp_dir):
       ...

The Python and R packages must give the same results. The shared test cases
are in ``parity`` and ``tests/test_parity.py`` runs them. If you change
a function that the R package also has, update both packages.

Documentation
-------------

The documentation is built with Sphinx from ``python/docs``:

.. code-block:: bash

   pip install -e ".[docs-build]"
   make docs-build                     # output in docs/_build/html

- Write pages in reStructuredText.
- Give each public function a docstring. The API reference comes from
  the docstrings.
- Add new public functions to ``varunayan/__init__.py`` and to
  ``docs/api_reference/*.rst``.
- Put notebooks in ``python/notebooks/``. ``docs/notebooks/`` links to them.

Pull Requests
-------------

1. Make a branch from ``develop``.
2. Make your changes. Add tests and update the documentation.
3. Make sure that the CI checks pass.
4. Open a pull request. Describe the change and refer to the issue, for
   example "Fixes #123".

Bug Reports
-----------

Include:

- Operating system, Python version and varunayan version
- The steps to reproduce the problem, with the expected and actual result
- The error message and stack trace
- A minimal example, for example:

.. code-block:: python

   from varunayan import era5ify_point

   era5ify_point(
       request_id="test",
       variables=["2m_temperature"],
       start_date="2020-01-01",
       end_date="2020-01-02",
       lat=40.0,
       lon=-120.0,
   )

Releases
--------

Releases use semantic versioning (MAJOR.MINOR.PATCH). MAJOR is for breaking
changes, MINOR is for new features and PATCH is for bug fixes. List each
change in ``docs/history.rst``.
