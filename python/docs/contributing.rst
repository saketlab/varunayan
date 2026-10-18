Contributing
============

We welcome contributions to varunayan! This guide will help you get started with contributing to the project.

Types of Contributions
----------------------

We welcome many types of contributions:

- **Bug reports** and **feature requests** via GitHub Issues
- **Code contributions** via Pull Requests
- **Documentation improvements** 
- **Tutorial and example notebooks**
- **Performance optimizations**
- **Test coverage improvements**

Development Setup
-----------------

Prerequisites
~~~~~~~~~~~~~

- Python 3.9 or higher
- Git
- A GitHub account

Getting Started
~~~~~~~~~~~~~~~

1. Fork the repository on GitHub
2. Clone your fork locally:

.. code-block:: bash

   git clone https://github.com/your-username/varunayan.git
   cd varunayan

3. Create a virtual environment:

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

4. Install in development mode:

.. code-block:: bash

   pip install -e ".[dev]"

5. Set up pre-commit hooks:

.. code-block:: bash

   pre-commit install

Development Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

The development installation includes:

- **pytest**: Testing framework
- **black**: Code formatting
- **isort**: Import sorting  
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks for code quality

Code Quality Standards
----------------------

We maintain high code quality standards through automated tools.

Code Formatting
~~~~~~~~~~~~~~~

We use **black** for code formatting with line length of 88 characters:

.. code-block:: bash

   # Format all code
   black varunayan/ tests/

   # Check formatting
   black --check varunayan/ tests/

Import Sorting
~~~~~~~~~~~~~~

We use **isort** to sort imports:

.. code-block:: bash

   # Sort imports
   isort varunayan/ tests/

   # Check import sorting
   isort --check-only varunayan/ tests/

Linting
~~~~~~~

We use **flake8** for linting:

.. code-block:: bash

   # Lint code
   flake8 varunayan/ tests/

Type Checking
~~~~~~~~~~~~~

We use **mypy** for static type checking:

.. code-block:: bash

   # Type check
   mypy varunayan/

Running Tests
-------------

Test Structure
~~~~~~~~~~~~~~

Tests are located in the ``tests/`` directory and use pytest:

.. code-block:: bash

   tests/
   ├── test_cli.py          # CLI functionality tests
   ├── test_core.py         # Core processing tests  
   ├── test_download.py     # Download functionality tests
   ├── test_processing.py   # Data processing tests
   ├── test_utils.py        # Utility function tests
   └── conftest.py          # Shared test fixtures

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   pytest

   # Run with coverage
   pytest --cov=varunayan

   # Run specific test file
   pytest tests/test_core.py

   # Run with verbose output
   pytest -v

Test Coverage
~~~~~~~~~~~~~

We aim for high test coverage. Check current coverage with:

.. code-block:: bash

   pytest --cov=varunayan --cov-report=html
   # Opens htmlcov/index.html in browser

Writing Tests
~~~~~~~~~~~~~

When adding new features, please include tests:

.. code-block:: python

   import pytest
   from varunayan.core import ProcessingParams, validate_inputs

   def test_validate_inputs_valid_params():
       """Test that valid parameters pass validation."""
       params = ProcessingParams(
           request_id="test",
           variables=["2m_temperature"],
           start_date=datetime(2020, 1, 1),
           end_date=datetime(2020, 1, 2),
           # ... other required params
       )
       # Should not raise any exceptions
       validate_inputs(params)

   def test_validate_inputs_invalid_dates():
       """Test that invalid date ranges are rejected."""
       params = ProcessingParams(
           request_id="test", 
           variables=["2m_temperature"],
           start_date=datetime(2020, 1, 2),  # After end_date
           end_date=datetime(2020, 1, 1),
           # ... other required params  
       )
       with pytest.raises(ValueError):
           validate_inputs(params)

Documentation
-------------

Documentation Structure
~~~~~~~~~~~~~~~~~~~~~~~

Documentation is built with Sphinx and hosted on GitHub Pages:

.. code-block::

   docs/
   ├── conf.py              # Sphinx configuration
   ├── index.rst            # Main documentation page
   ├── installation.rst     # Installation instructions
   ├── quickstart.rst       # Getting started guide
   ├── cli_reference.rst    # CLI documentation
   ├── examples.rst         # Usage examples
   ├── contributing.rst     # This file
   ├── api_reference.rst    # API documentation
   └── _static/             # Static assets

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Build documentation locally
   cd docs
   make html

   # View documentation
   open _build/html/index.html

Writing Documentation
~~~~~~~~~~~~~~~~~~~~~

- Use reStructuredText (.rst) format
- Include code examples with proper syntax highlighting
- Add docstrings to all public functions and classes
- Update relevant documentation when adding features

Pull Request Process
--------------------

Workflow
~~~~~~~~

1. Create a feature branch:

.. code-block:: bash

   git checkout -b feature/my-new-feature

2. Make your changes and commit:

.. code-block:: bash

   git add .
   git commit -m "Add new feature: brief description"

3. Push to your fork:

.. code-block:: bash

   git push origin feature/my-new-feature

4. Create a Pull Request on GitHub

PR Guidelines
~~~~~~~~~~~~~

- **Describe your changes clearly** in the PR description
- **Reference relevant issues** using "Fixes #123" or "Addresses #123"
- **Include tests** for new functionality
- **Update documentation** if needed
- **Ensure all CI checks pass**

PR Review Process
~~~~~~~~~~~~~~~~~

1. Automated checks run (tests, linting, type checking)
2. Maintainers review code and provide feedback
3. Address review comments and update PR
4. Once approved, maintainers will merge the PR

Code Review Checklist
~~~~~~~~~~~~~~~~~~~~~

Before submitting a PR, ensure:

- [ ] Code follows project style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No breaking changes (or properly documented)
- [ ] Commit messages are clear and descriptive

Bug Reports
-----------

When reporting bugs, please include:

**Environment Information**
- Operating system and version
- Python version
- varunayan version
- Relevant dependency versions

**Bug Description**
- Clear description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- Error messages and stack traces

**Minimal Example**
Provide a minimal code example that reproduces the bug:

.. code-block:: python

   from varunayan import era5ify_point

   # This should work but raises an error
   era5ify_point(
       request_id="test",
       variables=["2m_temperature"],
       start_date="2020-01-01",
       end_date="2020-01-02",
       latitude=40.0,
       longitude=-120.0
   )

Feature Requests
----------------

When requesting new features:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** clearly
3. **Explain why** the feature would be valuable
4. **Suggest implementation** approach if possible
5. **Consider backwards compatibility**

Release Process
---------------

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)  
- **PATCH**: Bug fixes (backwards compatible)

The release process is automated via GitHub Actions when tags are pushed.

Getting Help
------------

If you need help with contributing:

- Check existing **GitHub Issues** and **Discussions**
- Ask questions in **GitHub Discussions**
- Contact maintainers via **GitHub Issues**

We're here to help and appreciate all contributions to make varunayan better!