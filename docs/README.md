# Documentation Build Guide

This directory contains the Sphinx documentation for Varunayan, including a versioned changelog system.


## Building Documentation

### Standard Documentation (Current Version)

```bash
# Install documentation dependencies
pip install -e .[docs]

# Build documentation
cd docs
make html

# Serve locally
cd _build/html && python -m http.server 8000
```

### Versioned Documentation (All Versions)

```bash
# Build all versions (requires git tags)
python scripts/build_versioned_docs.py

# Or manually:
pip install -e .[docs]
sphinx-multiversion docs docs/_build/html
```

## Version Management

### Creating New Versions

1. **Tag your release**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Update changelog** in `docs/changelog.md`:
   ```markdown
   ## [1.0.0] - 2024-XX-XX
   
   ### Added
   - New feature descriptions
   
   ### Changed
   - Changes to existing features
   ```

3. **Update version in code**:
   - `pyproject.toml`: Update version number
   - `varunayan/__init__.py`: Update `__version__`
   - `docs/conf.py`: Update `release` variable

4. **Rebuild documentation**:
   ```bash
   python scripts/build_versioned_docs.py
   ```

### Version Switching

The documentation includes a version switcher that:
- Shows all available versions (tags + main branch)
- Allows users to switch between versions
- Maintains the same page when switching (when available)
- Configured in `docs/_static/versions.json`

## Changelog Management

### Format

The changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format:

- **Added**: New features
- **Changed**: Changes in existing functionality  
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

### Per-Version Changes

Each version gets its own section with:
- Release date
- Categorized changes
- Links to GitHub releases/tags
- Migration notes (if needed)

## Configuration Files

- `docs/conf.py`: Main Sphinx configuration with multiversion support
- `docs/_static/versions.json`: Version switcher configuration
- `docs/changelog.md`: Main changelog file
- `scripts/build_versioned_docs.py`: Automated build script

## Dependencies

Key documentation dependencies:
- `sphinx>=4.0`: Documentation generator
- `sphinx-book-theme>=1.0.0`: Modern theme
- `sphinx-multiversion>=0.2.4`: Version switching
- `myst-parser>=0.15`: Markdown support
- `myst-nb>=0.13.0`: Jupyter notebook support

## Deployment

For automated deployment (e.g., GitHub Actions):

```yaml
- name: Build versioned docs
  run: |
    pip install -e .[docs-build]
    python scripts/build_versioned_docs.py
    
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./docs/_build/html
```

## Troubleshooting

### Common Issues

1. **No versions showing**: Ensure you have git tags in format `v1.0.0`
2. **Build fails**: Check all dependencies are installed with `pip install -e .[docs]`
3. **Version switcher not working**: Verify `versions.json` is correctly formatted
4. **Changelog not updating**: Ensure changelog.md is included in toctree

### Debug Commands

```bash
# Check available tags
git tag -l 'v*'

# Test sphinx-multiversion
sphinx-multiversion --dump-metadata docs docs/_build/html

# Build with verbose output
sphinx-multiversion -v docs docs/_build/html
```
