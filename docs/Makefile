# Sphinx documentation Makefile
#
# This Makefile provides documentation-specific build targets

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD  ?= sphinx-build
SOURCEDIR    = .
BUILDDIR     = _build
JUPYTER      ?= jupyter
PYTHON       ?= python

# Put it first so that "make" without argument is like "make help".
help:
	@echo "Varunayan Documentation Makefile"
	@echo "================================"
	@echo ""
	@echo "Available targets:"
	@echo "  html        Build HTML documentation"
	@echo "  serve       Build and serve documentation locally"
	@echo "  clean       Clean build directory"
	@echo "  notebooks   Convert notebooks to markdown"
	@echo "  livehtml    Auto-rebuild HTML on changes"
	@echo "  linkcheck   Check all external links"
	@echo "  coverage    Check documentation coverage"
	@echo ""
	@echo "Sphinx standard targets:"
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Convert notebooks to markdown before building
.PHONY: notebooks
notebooks:
	@echo "Converting notebooks to markdown using automated script..."
	cd .. && $(PYTHON) scripts/convert_notebooks.py

# Build HTML documentation
.PHONY: html
html: notebooks
	@echo "Building HTML documentation..."
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)
	@echo "HTML documentation built in $(BUILDDIR)/html"

# Build and serve documentation locally
.PHONY: serve
serve: html
	@echo "Serving documentation at http://localhost:8000"
	@echo "Press Ctrl+C to stop the server"
	@cd $(BUILDDIR)/html && $(PYTHON) -m http.server 8000

# Auto-rebuild HTML on changes (requires sphinx-autobuild)
.PHONY: livehtml
livehtml: notebooks
	@echo "Starting live HTML build server..."
	@echo "Install sphinx-autobuild with: pip install sphinx-autobuild"
	@if command -v sphinx-autobuild >/dev/null 2>&1; then \
		sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O); \
	else \
		echo "sphinx-autobuild not found. Install with: pip install sphinx-autobuild"; \
		exit 1; \
	fi

# Check external links
.PHONY: linkcheck
linkcheck: notebooks
	@echo "Checking external links..."
	@$(SPHINXBUILD) -b linkcheck "$(SOURCEDIR)" "$(BUILDDIR)/linkcheck" $(SPHINXOPTS) $(O)

# Check documentation coverage
.PHONY: coverage
coverage: notebooks
	@echo "Checking documentation coverage..."
	@$(SPHINXBUILD) -b coverage "$(SOURCEDIR)" "$(BUILDDIR)/coverage" $(SPHINXOPTS) $(O)
	@echo "Coverage report generated in $(BUILDDIR)/coverage"

# Clean build directory
.PHONY: clean
clean:
	@echo "Cleaning build directory..."
	rm -rf $(BUILDDIR)/*
	rm -f tutorials/demo_tutorial_notebook.md
	rm -f tutorials/india_temperature_notebook.md

# Full clean including generated files
.PHONY: distclean
distclean: clean
	@echo "Cleaning all generated files..."
	rm -rf $(BUILDDIR)
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Build documentation for deployment (GitHub Pages style)
.PHONY: deploy
deploy: clean notebooks
	@echo "Building documentation for deployment..."
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)
	@echo "Documentation ready for deployment in $(BUILDDIR)/html"
	@echo "To test deployment locally, run: make serve"

# Quick build for development
.PHONY: quick
quick:
	@echo "Quick build (without notebook conversion)..."
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)

# Build all formats
.PHONY: all
all: html linkcheck coverage
	@echo "All documentation formats built successfully!"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
