"""
Optimized geometric operations for spatial data handling.

This module provides efficient geometric operations including
coordinate validation, bounding box extraction, and GeoJSON operations.
"""

import logging
from typing import Dict, List, Tuple, Union, Optional, Any
import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon, box
from shapely.ops import unary_union
import geopandas as gpd

from ..constants import MIN_LATITUDE, MAX_LATITUDE, MIN_LONGITUDE, MAX_LONGITUDE
from ..exceptions import ValidationError, GeospatialError

logger = logging.getLogger(__name__)


def validate_coordinates(
    latitude: float, 
    longitude: float,
    strict: bool = True
) -> bool:
    """
    Validate geographic coordinates.
    
    Args:
        latitude: Latitude value to validate
        longitude: Longitude value to validate  
        strict: If True, use strict bounds checking
        
    Returns:
        True if coordinates are valid
        
    Raises:
        ValidationError: If coordinates are invalid and strict=True
    """
    lat_valid = MIN_LATITUDE <= latitude <= MAX_LATITUDE
    
    # Handle longitude wrapping
    if longitude < MIN_LONGITUDE:
        longitude += 360
    elif longitude > MAX_LONGITUDE:
        longitude -= 360
    
    lon_valid = MIN_LONGITUDE <= longitude <= MAX_LONGITUDE
    
    valid = lat_valid and lon_valid
    
    if not valid and strict:
        raise ValidationError(
            f"Invalid coordinates: lat={latitude}, lon={longitude}",
            details={"latitude": latitude, "longitude": longitude}
        )
    
    return valid


def extract_coordinates_from_geometry(geometry: Dict[str, Any]) -> List[Tuple[float, float]]:
    """
    Extract all coordinate pairs from a GeoJSON geometry.
    
    Optimized version that handles all geometry types efficiently.
    
    Args:
        geometry: GeoJSON geometry dictionary
        
    Returns:
        List of (longitude, latitude) coordinate tuples
    """
    coords = []
    geom_type = geometry.get("type")
    
    if not geom_type:
        raise GeospatialError("Geometry missing 'type' field")
    
    coordinates = geometry.get("coordinates", [])
    
    try:
        if geom_type == "Point":
            coords.append(tuple(coordinates))
        
        elif geom_type == "MultiPoint":
            coords.extend(tuple(coord) for coord in coordinates)
        
        elif geom_type == "LineString":
            coords.extend(tuple(coord) for coord in coordinates)
        
        elif geom_type == "MultiLineString":
            for line in coordinates:
                coords.extend(tuple(coord) for coord in line)
        
        elif geom_type == "Polygon":
            # Only use exterior ring for efficiency
            coords.extend(tuple(coord) for coord in coordinates[0])
        
        elif geom_type == "MultiPolygon":
            for polygon in coordinates:
                # Only use exterior ring of each polygon
                coords.extend(tuple(coord) for coord in polygon[0])
        
        elif geom_type == "GeometryCollection":
            for geom in geometry.get("geometries", []):
                coords.extend(extract_coordinates_from_geometry(geom))
        
        else:
            raise GeospatialError(f"Unsupported geometry type: {geom_type}")
    
    except (IndexError, TypeError, ValueError) as e:
        raise GeospatialError(f"Invalid geometry structure: {e}")
    
    return coords


def extract_bounding_box(
    geojson_data: Dict[str, Any],
    buffer: Optional[float] = None
) -> Tuple[float, float, float, float]:
    """
    Extract bounding box from GeoJSON data with optional buffering.
    
    Optimized to handle large geometries efficiently.
    
    Args:
        geojson_data: GeoJSON object (Feature, FeatureCollection, or Geometry)
        buffer: Optional buffer distance in degrees
        
    Returns:
        Tuple of (west, south, east, north) coordinates
    """
    # Check for existing bbox
    if "bbox" in geojson_data:
        bbox = geojson_data["bbox"]
        if len(bbox) >= 4:
            west, south, east, north = bbox[:4]
            if buffer:
                west -= buffer
                south -= buffer
                east += buffer
                north += buffer
            return west, south, east, north
    
    # Extract coordinates based on GeoJSON type
    all_coords = []
    
    geojson_type = geojson_data.get("type")
    
    if geojson_type == "Feature":
        geometry = geojson_data.get("geometry")
        if geometry:
            all_coords.extend(extract_coordinates_from_geometry(geometry))
    
    elif geojson_type == "FeatureCollection":
        features = geojson_data.get("features", [])
        for feature in features:
            geometry = feature.get("geometry")
            if geometry:
                all_coords.extend(extract_coordinates_from_geometry(geometry))
    
    elif geojson_type in [
        "Point", "MultiPoint", "LineString", "MultiLineString", 
        "Polygon", "MultiPolygon", "GeometryCollection"
    ]:
        all_coords.extend(extract_coordinates_from_geometry(geojson_data))
    
    else:
        raise GeospatialError(f"Unsupported GeoJSON type: {geojson_type}")
    
    if not all_coords:
        raise GeospatialError("No coordinates found in GeoJSON data")
    
    # Calculate bounds efficiently using numpy
    coords_array = np.array(all_coords)
    lons = coords_array[:, 0]
    lats = coords_array[:, 1]
    
    west, east = float(np.min(lons)), float(np.max(lons))
    south, north = float(np.min(lats)), float(np.max(lats))
    
    # Apply buffer if specified
    if buffer:
        west -= buffer
        south -= buffer
        east += buffer
        north += buffer
    
    # Validate bounds
    if not (MIN_LATITUDE <= south <= north <= MAX_LATITUDE):
        logger.warning(f"Latitude bounds may be invalid: {south} to {north}")
    
    return west, south, east, north


def create_geojson_polygon(
    coordinates: List[List[Tuple[float, float]]],
    properties: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a GeoJSON polygon feature.
    
    Args:
        coordinates: List of coordinate rings (exterior + holes)
        properties: Optional properties dictionary
        
    Returns:
        GeoJSON Feature with Polygon geometry
    """
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": coordinates
        },
        "properties": properties or {}
    }


def create_bounding_box_geojson(
    west: float,
    south: float, 
    east: float,
    north: float,
    properties: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a GeoJSON polygon from bounding box coordinates.
    
    Args:
        west, south, east, north: Bounding box coordinates
        properties: Optional properties dictionary
        
    Returns:
        GeoJSON Feature with bounding box polygon
    """
    coordinates = [[
        [west, south],
        [east, south], 
        [east, north],
        [west, north],
        [west, south]  # Close the polygon
    ]]
    
    default_properties = {
        "type": "bounding_box",
        "bounds": {"west": west, "south": south, "east": east, "north": north}
    }
    
    if properties:
        default_properties.update(properties)
    
    return create_geojson_polygon(coordinates, default_properties)


def simplify_geometry(
    geometry: Union[Polygon, MultiPolygon],
    tolerance: float = 0.01,
    preserve_topology: bool = True
) -> Union[Polygon, MultiPolygon]:
    """
    Simplify geometry for improved performance.
    
    Args:
        geometry: Shapely geometry to simplify
        tolerance: Simplification tolerance in degrees
        preserve_topology: Whether to preserve topology during simplification
        
    Returns:
        Simplified geometry
    """
    try:
        if preserve_topology:
            return geometry.simplify(tolerance, preserve_topology=True)
        else:
            return geometry.simplify(tolerance)
    except Exception as e:
        logger.warning(f"Geometry simplification failed: {e}")
        return geometry


def create_spatial_index(geometries: List[Union[Polygon, MultiPolygon]]) -> gpd.GeoDataFrame:
    """
    Create a spatial index for efficient geometric operations.
    
    Args:
        geometries: List of geometries to index
        
    Returns:
        GeoDataFrame with spatial index
    """
    gdf = gpd.GeoDataFrame(
        {'id': range(len(geometries))},
        geometry=geometries,
        crs='EPSG:4326'
    )
    
    # Build spatial index
    gdf.sindex
    
    return gdf


def buffer_geometry(
    geometry: Union[Polygon, MultiPolygon],
    distance: float,
    resolution: int = 16
) -> Union[Polygon, MultiPolygon]:
    """
    Buffer a geometry by a specified distance.
    
    Args:
        geometry: Geometry to buffer
        distance: Buffer distance in degrees
        resolution: Number of segments for circular buffers
        
    Returns:
        Buffered geometry
    """
    try:
        return geometry.buffer(distance, resolution=resolution)
    except Exception as e:
        raise GeospatialError(f"Geometry buffering failed: {e}")


def intersect_geometries(
    geom1: Union[Polygon, MultiPolygon],
    geom2: Union[Polygon, MultiPolygon]
) -> Union[Polygon, MultiPolygon, None]:
    """
    Compute intersection of two geometries.
    
    Args:
        geom1: First geometry
        geom2: Second geometry
        
    Returns:
        Intersection geometry or None if no intersection
    """
    try:
        intersection = geom1.intersection(geom2)
        return intersection if not intersection.is_empty else None
    except Exception as e:
        logger.warning(f"Geometry intersection failed: {e}")
        return None


def merge_geometries(geometries: List[Union[Polygon, MultiPolygon]]) -> Union[Polygon, MultiPolygon]:
    """
    Merge multiple geometries into a single geometry.
    
    Args:
        geometries: List of geometries to merge
        
    Returns:
        Merged geometry
    """
    if not geometries:
        raise GeospatialError("No geometries provided for merging")
    
    if len(geometries) == 1:
        return geometries[0]
    
    try:
        return unary_union(geometries)
    except Exception as e:
        raise GeospatialError(f"Geometry merging failed: {e}")


def validate_geojson_geometry(geometry: Dict[str, Any]) -> bool:
    """
    Validate a GeoJSON geometry structure.
    
    Args:
        geometry: GeoJSON geometry dictionary
        
    Returns:
        True if geometry is valid
    """
    required_fields = ["type", "coordinates"]
    
    # Check required fields
    for field in required_fields:
        if field not in geometry:
            return False
    
    # Check geometry type
    valid_types = [
        "Point", "MultiPoint", "LineString", "MultiLineString",
        "Polygon", "MultiPolygon", "GeometryCollection"
    ]
    
    if geometry["type"] not in valid_types:
        return False
    
    # Basic coordinate validation
    try:
        coords = extract_coordinates_from_geometry(geometry)
        if not coords:
            return False
        
        # Validate each coordinate pair
        for lon, lat in coords:
            if not validate_coordinates(lat, lon, strict=False):
                return False
        
        return True
    
    except (GeospatialError, Exception):
        return False