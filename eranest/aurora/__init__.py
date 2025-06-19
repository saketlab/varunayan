"""
Aurora integration module for Microsoft Aurora weather model.

This module handles conversion of ERA5 data to Aurora-compatible formats
and provides utilities for working with Aurora models.
"""

from .conversion import (
    AuroraConverter,
    era5_to_aurora_format,
    create_aurora_batch,
)

__all__ = [
    "AuroraConverter",
    "era5_to_aurora_format", 
    "create_aurora_batch",
]