"""
Utilities module for common functionality.

This module contains utility functions for file I/O, validation,
and other common operations used throughout the package.
"""

from .io import (
    extract_archive,
    find_files_by_pattern,
    load_json_file,
    save_json_file,
)
from .validation import (
    validate_coordinates,
    validate_date_range,
    validate_geojson,
    validate_variables,
)

__all__ = [
    "load_json_file",
    "save_json_file",
    "extract_archive",
    "find_files_by_pattern",
    "validate_date_range",
    "validate_coordinates",
    "validate_variables",
    "validate_geojson",
]
