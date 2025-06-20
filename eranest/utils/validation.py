"""
Validation utilities for data and parameter validation.

This module provides comprehensive validation functions for
dates, coordinates, variables, and data structures.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from ..constants import (
    DEFAULT_ATMOSPHERIC_VARIABLES,
    DEFAULT_STATIC_VARIABLES,
    DEFAULT_SURFACE_VARIABLES,
    ERROR_MESSAGES,
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MAX_PRESSURE_LEVEL,
    MIN_LATITUDE,
    MIN_LONGITUDE,
    MIN_PRESSURE_LEVEL,
    SUPPORTED_RESOLUTIONS,
    DataFrequency,
)
from ..exceptions import ValidationError

logger = logging.getLogger(__name__)


def parse_date(date_input: Union[str, datetime]) -> datetime:
    """
    Parse date from string or datetime object.
    
    Args:
        date_input: Date as string (YYYY-MM-DD or YYYY-MM-DD HH:MM) or datetime
        
    Returns:
        Parsed datetime object
        
    Raises:
        ValidationError: If date format is invalid
    """
    if isinstance(date_input, datetime):
        return date_input
    
    if isinstance(date_input, str):
        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d',
            '%Y/%m/%d %H:%M',
            '%Y/%m/%d %H:%M:%S',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%dT%H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_input, fmt)
            except ValueError:
                continue
        
        raise ValidationError(f"Unable to parse date: {date_input}")
    
    raise ValidationError(f"Invalid date type: {type(date_input)}")


def extract_bbox_from_geometry(geometry: Dict[str, Any]) -> Tuple[float, float, float, float]:
    """
    Extract bounding box from GeoJSON geometry.
    
    Args:
        geometry: GeoJSON-like geometry dictionary
        
    Returns:
        Tuple of (north, west, south, east) coordinates
        
    Raises:
        ValidationError: If geometry is invalid
    """
    try:
        if 'features' in geometry:
            # FeatureCollection
            features = geometry['features']
            if not features:
                raise ValidationError("No features found in geometry")
            
            # Get bounds from all features
            all_coords = []
            for feature in features:
                coords = _extract_coordinates(feature['geometry'])
                all_coords.extend(coords)
                
        elif 'geometry' in geometry:
            # Single Feature
            all_coords = _extract_coordinates(geometry['geometry'])
        else:
            # Direct geometry
            all_coords = _extract_coordinates(geometry)
        
        if not all_coords:
            raise ValidationError("No coordinates found in geometry")
        
        # Calculate bounding box
        lons = [coord[0] for coord in all_coords]
        lats = [coord[1] for coord in all_coords]
        
        west, east = min(lons), max(lons)
        south, north = min(lats), max(lats)
        
        # Add small buffer
        buffer = 0.1
        north += buffer
        south -= buffer
        east += buffer
        west -= buffer
        
        return north, west, south, east
        
    except Exception as e:
        raise ValidationError(f"Failed to extract bounding box from geometry: {e}")


def _extract_coordinates(geometry: Dict[str, Any]) -> List[Tuple[float, float]]:
    """Extract all coordinates from a geometry object."""
    coords = []
    geom_type = geometry.get('type', '')
    coordinates = geometry.get('coordinates', [])
    
    if geom_type == 'Point':
        coords.append(tuple(coordinates))
    elif geom_type in ['LineString', 'MultiPoint']:
        coords.extend([tuple(coord) for coord in coordinates])
    elif geom_type in ['Polygon', 'MultiLineString']:
        for ring in coordinates:
            coords.extend([tuple(coord) for coord in ring])
    elif geom_type == 'MultiPolygon':
        for polygon in coordinates:
            for ring in polygon:
                coords.extend([tuple(coord) for coord in ring])
    
    return coords


def validate_date_range(
    start_date: datetime,
    end_date: datetime,
    max_range_days: Optional[int] = None,
    min_range_hours: Optional[int] = None,
) -> bool:
    """
    Validate date range parameters.

    Args:
        start_date: Start date
        end_date: End date
        max_range_days: Maximum allowed range in days
        min_range_hours: Minimum required range in hours

    Returns:
        True if date range is valid

    Raises:
        ValidationError: If date range is invalid
    """
    if start_date > end_date:
        raise ValidationError(
            ERROR_MESSAGES["invalid_date_range"],
            details={"start": start_date, "end": end_date},
        )

    # Check maximum range
    if max_range_days:
        max_delta = timedelta(days=max_range_days)
        if (end_date - start_date) > max_delta:
            raise ValidationError(
                f"Date range exceeds maximum allowed range of {max_range_days} days",
                details={
                    "range_days": (end_date - start_date).days,
                    "max_days": max_range_days,
                },
            )

    # Check minimum range
    if min_range_hours:
        min_delta = timedelta(hours=min_range_hours)
        if (end_date - start_date) < min_delta:
            raise ValidationError(
                f"Date range is less than minimum required range of {min_range_hours} hours",
                details={
                    "range_hours": (end_date - start_date).total_seconds() / 3600,
                    "min_hours": min_range_hours,
                },
            )

    # Check if dates are not too far in the future
    max_future_date = datetime.now() + timedelta(days=7)  # 1 week ahead
    if start_date > max_future_date:
        logger.warning(f"Start date is far in the future: {start_date}")

    # Check if dates are not too far in the past (ERA5 starts from 1940)
    min_past_date = datetime(1940, 1, 1)
    if start_date < min_past_date:
        raise ValidationError(
            f"Start date is before ERA5 data availability (1940-01-01): {start_date}",
            details={"start": start_date, "min_date": min_past_date},
        )

    return True


def validate_coordinates(
    latitude: Union[float, List[float], np.ndarray],
    longitude: Union[float, List[float], np.ndarray],
    strict: bool = True,
) -> bool:
    """
    Validate geographic coordinates.

    Args:
        latitude: Latitude value(s) to validate
        longitude: Longitude value(s) to validate
        strict: If True, raise exception on invalid coordinates

    Returns:
        True if all coordinates are valid

    Raises:
        ValidationError: If coordinates are invalid and strict=True
    """
    # Convert to arrays for uniform handling
    if isinstance(latitude, (int, float)):
        lats = np.array([latitude])
        lons = np.array([longitude])
    else:
        lats = np.array(latitude)
        lons = np.array(longitude)

    if len(lats) != len(lons):
        raise ValidationError(
            "Latitude and longitude arrays must have the same length",
            details={"lat_count": len(lats), "lon_count": len(lons)},
        )

    # Validate latitudes
    invalid_lats = (lats < MIN_LATITUDE) | (lats > MAX_LATITUDE)
    if np.any(invalid_lats):
        invalid_indices = np.where(invalid_lats)[0]
        if strict:
            raise ValidationError(
                f"Invalid latitude values at indices {invalid_indices.tolist()}",
                details={
                    "invalid_lats": lats[invalid_lats].tolist(),
                    "indices": invalid_indices.tolist(),
                },
            )
        return False

    # Handle longitude wrapping
    lons_wrapped = np.copy(lons)
    lons_wrapped[lons_wrapped < MIN_LONGITUDE] += 360
    lons_wrapped[lons_wrapped > MAX_LONGITUDE] -= 360

    # Validate wrapped longitudes
    invalid_lons = (lons_wrapped < MIN_LONGITUDE) | (lons_wrapped > MAX_LONGITUDE)
    if np.any(invalid_lons):
        invalid_indices = np.where(invalid_lons)[0]
        if strict:
            raise ValidationError(
                f"Invalid longitude values at indices {invalid_indices.tolist()}",
                details={
                    "invalid_lons": lons[invalid_lons].tolist(),
                    "indices": invalid_indices.tolist(),
                },
            )
        return False

    return True


def validate_bounding_box(
    north: float, west: float, south: float, east: float, strict: bool = True
) -> bool:
    """
    Validate bounding box coordinates.

    Args:
        north, west, south, east: Bounding box coordinates
        strict: If True, raise exception on invalid bounds

    Returns:
        True if bounding box is valid

    Raises:
        ValidationError: If bounding box is invalid and strict=True
    """
    # Validate individual coordinates
    try:
        validate_coordinates([north, south], [west, east], strict=True)
    except ValidationError as e:
        if strict:
            raise ValidationError(f"Invalid bounding box coordinates: {e}")
        return False

    # Check that north > south
    if north <= south:
        if strict:
            raise ValidationError(
                "North coordinate must be greater than south coordinate",
                details={"north": north, "south": south},
            )
        return False

    # Check longitude range (allow for crossing 180°)
    if east < west:
        # Crossing 180° meridian - this is valid
        logger.debug("Bounding box crosses 180° meridian")
    elif east - west > 360:
        if strict:
            raise ValidationError(
                "Bounding box longitude range cannot exceed 360°",
                details={"west": west, "east": east, "range": east - west},
            )
        return False

    # Check for reasonable size
    lat_range = north - south
    if lat_range > 180:
        if strict:
            raise ValidationError(
                "Bounding box latitude range cannot exceed 180°",
                details={"north": north, "south": south, "range": lat_range},
            )
        return False

    return True


def validate_variables(
    variables: List[str], variable_type: str, strict: bool = True
) -> bool:
    """
    Validate variable names against known variable sets.

    Args:
        variables: List of variable names to validate
        variable_type: Type of variables ("surface", "atmospheric", "static")
        strict: If True, raise exception on unknown variables

    Returns:
        True if all variables are valid

    Raises:
        ValidationError: If variables are invalid and strict=True
    """
    if not variables:
        if strict:
            raise ValidationError("At least one variable must be specified")
        return False

    # Get reference variable set
    if variable_type.lower() == "surface":
        reference_vars = set(DEFAULT_SURFACE_VARIABLES)
    elif variable_type.lower() == "atmospheric":
        reference_vars = set(DEFAULT_ATMOSPHERIC_VARIABLES)
    elif variable_type.lower() == "static":
        reference_vars = set(DEFAULT_STATIC_VARIABLES)
    else:
        if strict:
            raise ValidationError(f"Unknown variable type: {variable_type}")
        return False

    # Check for unknown variables
    unknown_vars = set(variables) - reference_vars
    if unknown_vars:
        if strict:
            raise ValidationError(
                f"Unknown {variable_type} variables: {list(unknown_vars)}",
                details={
                    "unknown_variables": list(unknown_vars),
                    "valid_variables": list(reference_vars),
                },
            )
        else:
            logger.warning(f"Unknown {variable_type} variables: {list(unknown_vars)}")
            return False

    return True


def validate_pressure_levels(
    pressure_levels: List[Union[str, int, float]], strict: bool = True
) -> bool:
    """
    Validate pressure level values.

    Args:
        pressure_levels: List of pressure levels to validate
        strict: If True, raise exception on invalid levels

    Returns:
        True if all pressure levels are valid

    Raises:
        ValidationError: If pressure levels are invalid and strict=True
    """
    if not pressure_levels:
        if strict:
            raise ValidationError("At least one pressure level must be specified")
        return False

    # Convert to numeric values
    try:
        numeric_levels = [float(level) for level in pressure_levels]
    except (ValueError, TypeError) as e:
        if strict:
            raise ValidationError(f"Invalid pressure level values: {e}")
        return False

    # Check range
    for level in numeric_levels:
        if not (MIN_PRESSURE_LEVEL <= level <= MAX_PRESSURE_LEVEL):
            if strict:
                raise ValidationError(
                    f"Pressure level {level} hPa is outside valid range "
                    f"({MIN_PRESSURE_LEVEL}-{MAX_PRESSURE_LEVEL} hPa)",
                    details={
                        "invalid_level": level,
                        "min": MIN_PRESSURE_LEVEL,
                        "max": MAX_PRESSURE_LEVEL,
                    },
                )
            return False

    # Check for reasonable ordering (decreasing pressure = increasing altitude)
    sorted_levels = sorted(numeric_levels, reverse=True)
    if sorted_levels != numeric_levels:
        logger.warning("Pressure levels are not in descending order (surface to top)")

    return True


def validate_resolution(resolution: float, strict: bool = True) -> bool:
    """
    Validate grid resolution.

    Args:
        resolution: Grid resolution in degrees
        strict: If True, raise exception on invalid resolution

    Returns:
        True if resolution is valid

    Raises:
        ValidationError: If resolution is invalid and strict=True
    """
    if resolution <= 0:
        if strict:
            raise ValidationError(
                f"Resolution must be positive, got {resolution}",
                details={"resolution": resolution},
            )
        return False

    if resolution > 5.0:
        if strict:
            raise ValidationError(
                f"Resolution {resolution}° is very coarse (>5°), this may not be intended",
                details={"resolution": resolution, "max_reasonable": 5.0},
            )
        else:
            logger.warning(f"Very coarse resolution: {resolution}°")

    # Check against supported resolutions
    if resolution not in SUPPORTED_RESOLUTIONS:
        logger.info(
            f"Resolution {resolution}° is not in standard list: {SUPPORTED_RESOLUTIONS}"
        )

    return True


def validate_frequency(
    frequency: Union[str, DataFrequency], strict: bool = True
) -> bool:
    """
    Validate data frequency parameter.

    Args:
        frequency: Data frequency to validate
        strict: If True, raise exception on invalid frequency

    Returns:
        True if frequency is valid

    Raises:
        ValidationError: If frequency is invalid and strict=True
    """
    if isinstance(frequency, str):
        try:
            DataFrequency(frequency.lower())
        except ValueError:
            valid_frequencies = [f.value for f in DataFrequency]
            if strict:
                raise ValidationError(
                    f"Invalid frequency '{frequency}', must be one of: {valid_frequencies}",
                    details={
                        "frequency": frequency,
                        "valid_frequencies": valid_frequencies,
                    },
                )
            return False
    elif not isinstance(frequency, DataFrequency):
        if strict:
            raise ValidationError(
                f"Frequency must be string or DataFrequency enum, got {type(frequency)}"
            )
        return False

    return True


def validate_geojson(geojson_data: Dict[str, Any], strict: bool = True) -> bool:
    """
    Validate GeoJSON structure and content.

    Args:
        geojson_data: GeoJSON data to validate
        strict: If True, raise exception on invalid GeoJSON

    Returns:
        True if GeoJSON is valid

    Raises:
        ValidationError: If GeoJSON is invalid and strict=True
    """
    if not isinstance(geojson_data, dict):
        if strict:
            raise ValidationError("GeoJSON must be a dictionary")
        return False

    # Check required 'type' field
    if "type" not in geojson_data:
        if strict:
            raise ValidationError("GeoJSON missing required 'type' field")
        return False

    geojson_type = geojson_data["type"]
    valid_types = [
        "Feature",
        "FeatureCollection",
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
        "GeometryCollection",
    ]

    if geojson_type not in valid_types:
        if strict:
            raise ValidationError(
                f"Invalid GeoJSON type '{geojson_type}', must be one of: {valid_types}",
                details={"type": geojson_type, "valid_types": valid_types},
            )
        return False

    # Validate structure based on type
    if geojson_type == "FeatureCollection":
        if "features" not in geojson_data:
            if strict:
                raise ValidationError("FeatureCollection missing 'features' array")
            return False

        if not isinstance(geojson_data["features"], list):
            if strict:
                raise ValidationError("FeatureCollection 'features' must be an array")
            return False

        # Validate each feature
        for i, feature in enumerate(geojson_data["features"]):
            if not validate_geojson(feature, strict=False):
                if strict:
                    raise ValidationError(f"Invalid feature at index {i}")
                return False

    elif geojson_type == "Feature":
        required_fields = ["geometry", "properties"]
        for field in required_fields:
            if field not in geojson_data:
                if strict:
                    raise ValidationError(f"Feature missing required '{field}' field")
                return False

        # Validate geometry
        if geojson_data["geometry"] is not None:
            if not validate_geojson(geojson_data["geometry"], strict=False):
                if strict:
                    raise ValidationError("Feature has invalid geometry")
                return False

    elif geojson_type in [
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
    ]:
        if "coordinates" not in geojson_data:
            if strict:
                raise ValidationError(f"{geojson_type} missing 'coordinates' field")
            return False

        # Basic coordinate validation
        try:
            coords = geojson_data["coordinates"]
            if geojson_type == "Point":
                if len(coords) < 2:
                    raise ValidationError(
                        "Point coordinates must have at least 2 elements"
                    )
                validate_coordinates(coords[1], coords[0], strict=True)
            # Additional coordinate validation could be added here
        except (TypeError, IndexError, ValidationError) as e:
            if strict:
                raise ValidationError(f"Invalid coordinates in {geojson_type}: {e}")
            return False

    return True


def validate_request_id(request_id: str, strict: bool = True) -> bool:
    """
    Validate request ID format.

    Args:
        request_id: Request ID to validate
        strict: If True, raise exception on invalid ID

    Returns:
        True if request ID is valid

    Raises:
        ValidationError: If request ID is invalid and strict=True
    """
    if not request_id:
        if strict:
            raise ValidationError("Request ID cannot be empty")
        return False

    if not isinstance(request_id, str):
        if strict:
            raise ValidationError(f"Request ID must be string, got {type(request_id)}")
        return False

    # Check for invalid characters
    invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    for char in invalid_chars:
        if char in request_id:
            if strict:
                raise ValidationError(
                    f"Request ID contains invalid character '{char}'",
                    details={"request_id": request_id, "invalid_chars": invalid_chars},
                )
            return False

    # Check length
    if len(request_id) > 100:
        if strict:
            raise ValidationError(
                f"Request ID too long ({len(request_id)} characters), maximum is 100",
                details={"request_id": request_id, "length": len(request_id)},
            )
        return False

    return True


def validate_dataframe_structure(
    df: pd.DataFrame, required_columns: List[str], strict: bool = True
) -> bool:
    """
    Validate DataFrame structure and required columns.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        strict: If True, raise exception on validation failure

    Returns:
        True if DataFrame structure is valid

    Raises:
        ValidationError: If DataFrame is invalid and strict=True
    """
    if df.empty:
        if strict:
            raise ValidationError("DataFrame is empty")
        return False

    # Check required columns
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        if strict:
            raise ValidationError(
                f"DataFrame missing required columns: {list(missing_columns)}",
                details={
                    "missing_columns": list(missing_columns),
                    "available_columns": list(df.columns),
                },
            )
        return False

    # Check for NaN values in critical columns
    for col in required_columns:
        if df[col].isna().any():
            nan_count = df[col].isna().sum()
            if strict:
                raise ValidationError(
                    f"Column '{col}' contains {nan_count} NaN values",
                    details={
                        "column": col,
                        "nan_count": nan_count,
                        "total_rows": len(df),
                    },
                )
            else:
                logger.warning(f"Column '{col}' contains {nan_count} NaN values")

    return True
