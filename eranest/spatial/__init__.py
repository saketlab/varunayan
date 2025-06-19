"""
Spatial operations module for geographic data handling.

This module handles all geospatial operations including
coordinate transformations, spatial filtering, and geometry operations.
"""

from .geometry import (
    extract_bounding_box,
    create_geojson_polygon,
    validate_coordinates,
)
from .filtering import (
    SpatialFilter,
    filter_by_geometry,
    optimize_spatial_filtering,
)

__all__ = [
    "extract_bounding_box",
    "create_geojson_polygon",
    "validate_coordinates",
    "SpatialFilter",
    "filter_by_geometry",
    "optimize_spatial_filtering",
]