# Varunayan Project Makefile
# 

# Variables
PYTHON := python
PIP := pip
PYTEST := pytest
SPHINX_BUILD := sphinx-build
JUPYTER := jupyter
BLACK := black
ISORT := isort
FLAKE8 := flake8
MYPY := mypy

# Directories
DOCS_DIR := docs
NOTEBOOKS_DIR := notebooks
BUILD_DIR := build
DIST_DIR := dist
DOCS_BUILD_DIR := $(DOCS_DIR)/_build

# Default target
.PHONY: help
help:
	@echo "Varunayan Project Makefile"
	@echo "=========================="
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "Installation:"
	@echo "  install            Install package in editable mode"
	@echo "  install-dev        Install package in development mode with all dependencies"
	@echo "  install-docs       Install full documentation dependencies"
	@echo "  install-docs-build Install minimal documentation build dependencies"
	@echo "  install-docs-serve Install documentation serving dependencies"
	@echo "  install-build      Install build/distribution dependencies"
	@echo "  format          Format code with black and isort"
	@echo "  lint            Run linting with flake8"
	@echo "  typecheck       Run type checking with mypy"
	@echo "  test            Run all tests with pytest"
	@echo "  test-cov        Run tests with coverage reporting"
	@echo "  quality         Run all quality checks (format, lint, typecheck, test)"
	@echo ""
	@echo "Documentation:"
	@echo "  docs-clean      Clean documentation build directory"
	@echo "  docs-build      Build documentation with Sphinx"
	@echo "  docs-serve      Build and serve documentation locally"
	@echo "  docs-deploy     Build documentation as it would be deployed"
	@echo "  docs-all        Full documentation build pipeline"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  build           Build distribution packages"
	@echo "  clean           Clean all build artifacts"
	@echo "  dist-check      Check distribution packages"
	@echo "  upload          Upload distribution packages to PyPI"
	@echo ""
	@echo "CI Simulation:"
	@echo "  ci-local        Simulate CI pipeline locally"
	@echo "  ci-docs         Simulate documentation CI pipeline"
	@echo ""
	@echo "Maintenance:"
	@echo "  deps-update     Update dependencies"
	@echo "  pre-commit      Run pre-commit hooks"

# Installation targets
.PHONY: install
install:
	@echo "Installing varunayan package..."
	$(PIP) install -e .

.PHONY: install-dev
install-dev:
	@echo "Installing development dependencies..."
	$(PIP) install -e .[dev,quality,test]

.PHONY: install-docs
install-docs:
	@echo "Installing documentation dependencies..."
	$(PIP) install -e .[docs]

.PHONY: install-docs-build
install-docs-build:
	@echo "Installing minimal documentation build dependencies..."
	$(PIP) install -e .[docs-build]

.PHONY: install-docs-serve
install-docs-serve:
	@echo "Installing documentation serving dependencies..."
	$(PIP) install -e .[docs-serve]

.PHONY: install-build
install-build:
	@echo "Installing build dependencies..."
	$(PIP) install -e .[build]

.PHONY: format
format:
	@echo "Formatting code with black and isort..."
	$(BLACK) varunayan tests
	$(ISORT) varunayan tests

.PHONY: lint
lint:
	@echo "Running linting with flake8..."
	$(FLAKE8) varunayan tests

.PHONY: typecheck
typecheck:
	@echo "Running type checking with mypy..."
	$(MYPY) varunayan/

.PHONY: test
test:
	@echo "Running tests with pytest..."
	$(PYTEST)

.PHONY: test-cov
test-cov:
	@echo "Running tests with coverage..."
	$(PYTEST) --cov=varunayan --cov-report=html --cov-report=term-missing --cov-report=xml

.PHONY: quality
quality: format lint typecheck test
	@echo "All quality checks completed!"

# Documentation targets
.PHONY: docs-clean
docs-clean:
	@echo "Cleaning documentation build directory..."
	rm -rf $(DOCS_BUILD_DIR)

.PHONY: docs-build
docs-build:
	@echo "Building documentation with Sphinx..."
	cd $(DOCS_DIR); $(SPHINX_BUILD) -b html . _build/html

.PHONY: docs-serve
docs-serve: docs-build
	@echo "Serving documentation locally..."
	@echo "Documentation will be available at: http://localhost:8000"
	@echo "Press Ctrl+C to stop the server"
	cd $(DOCS_BUILD_DIR)/html; $(PYTHON) -m http.server 8000

.PHONY: docs-deploy
docs-deploy: docs-clean install-docs-build docs-build
	@echo "Building documentation for deployment..."
	@echo "Documentation built successfully!"
	@echo "Built files are in: $(DOCS_BUILD_DIR)/html"
	@echo "To preview, run: make docs-serve"

.PHONY: docs-all
docs-all: docs-clean install-docs docs-build
	@echo "Complete documentation build pipeline finished!"
	@echo "Run 'make docs-serve' to preview the documentation"

# Build & Deploy targets
.PHONY: build
build:
	@echo "Building distribution packages..."
	$(PYTHON) -m build

.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(BUILD_DIR)
	rm -rf $(DIST_DIR)
	rm -rf $(DOCS_BUILD_DIR)
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

.PHONY: dist-check
dist-check: build
	@echo "Checking distribution packages..."
	$(PYTHON) -m twine check $(DIST_DIR)/*

.PHONY: upload
upload: dist-check
	@echo "Uploading distribution packages to PyPI..."
	$(PYTHON) -m twine upload $(DIST_DIR)/*

# CI Simulation targets
.PHONY: ci-local
ci-local: clean install-dev quality build dist-check
	@echo "Local CI simulation completed successfully!"
	@echo "All checks passed - ready for CI/CD pipeline"

.PHONY: ci-docs
ci-docs: clean install-docs-build docs-deploy
	@echo "Documentation CI simulation completed successfully!"
	@echo "Documentation ready for deployment"

# Maintenance targets
.PHONY: deps-update
deps-update:
	@echo "Updating dependencies..."
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install --upgrade -e .[all]

.PHONY: pre-commit
pre-commit:
	@echo "Running pre-commit hooks..."
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit run --all-files; \
	else \
		echo "pre-commit not installed. Install with: pip install pre-commit"; \
	fi

# Testing and preview scripts
.PHONY: test-build
test-build:
	@echo "Running build test suite..."
	$(PYTHON) scripts/test_build.py

.PHONY: preview-docs
preview-docs:
	@echo "Starting documentation preview..."
	$(PYTHON) scripts/preview_docs.py

.PHONY: preview-docs-quick
preview-docs-quick:
	@echo "Starting quick documentation preview..."
	$(PYTHON) scripts/preview_docs.py --quick

.PHONY: test-workflows
test-workflows:
	@echo "Testing GitHub Actions workflows..."
	$(PYTHON) scripts/test_github_actions.py

# Special targets for different workflows
.PHONY: github-pages
github-pages: docs-deploy
	@echo "GitHub Pages build completed!"
	@echo "Upload the contents of $(DOCS_BUILD_DIR)/html to GitHub Pages"

.PHONY: quick-check
quick-check: format lint test
	@echo "Quick quality check completed!"

.PHONY: full-check
full-check: ci-local ci-docs
	@echo "Full project check completed!"
	@echo "Ready for production deployment"

# Development workflow targets
.PHONY: dev-setup
dev-setup: install-dev install-docs
	@echo "Development environment setup completed!"
	@echo "You can now run: make quality && make docs-serve"

.PHONY: dev-workflow
dev-workflow: format test docs-build
	@echo "Development workflow completed!"
	@echo "Code formatted, tests passed, docs built"

# Watch targets (requires inotify-tools on Linux or fswatch on macOS)
.PHONY: watch-docs
watch-docs:
	@echo "Watching for changes and rebuilding docs..."
	@echo "Install fswatch (macOS: brew install fswatch) or inotify-tools (Linux) for auto-rebuild"
	@while true; do \
		$(MAKE) docs-build; \
		sleep 2; \
	done

# Help for specific sections
.PHONY: help-dev
help-dev:
	@echo "Development Workflow:"
	@echo "1. make dev-setup     # First time setup"
	@echo "2. make dev-workflow  # Regular development cycle"
	@echo "3. make quality       # Before committing"
	@echo "4. make ci-local      # Before pushing"

.PHONY: help-docs
help-docs:
	@echo "Documentation Workflow:"
	@echo "1. make docs-all      # Build complete documentation"
	@echo "2. make docs-serve    # Preview documentation locally"
	@echo "3. make ci-docs       # Test documentation deployment"
	@echo "4. make github-pages  # Prepare for GitHub Pages"

# Ensure directories exist
$(DOCS_BUILD_DIR):
	mkdir -p $(DOCS_BUILD_DIR)

build-dir:
	mkdir -p $(BUILD_DIR)

dist-dir:
	mkdir -p $(DIST_DIR)
