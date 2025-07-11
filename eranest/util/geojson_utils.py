import json
import os
import tempfile
from typing import Dict, Any, List, Tuple
import logging
from .logging_utils import get_logger

logger = get_logger(level=logging.INFO)

def extract_coords_from_geometry(geometry: Dict) -> List[List[float]]:
    """Extract all coordinates from a GeoJSON geometry object."""
    coords = []
    geom_type = geometry["type"]

    if geom_type == "Point":
        # Convert [lon, lat] to [lon, lat] (no change needed, but be explicit)
        coords.append(geometry["coordinates"])
    elif geom_type == "MultiPoint" or geom_type == "LineString":
        coords.extend(geometry["coordinates"])
    elif geom_type == "MultiLineString" or geom_type == "Polygon":
        for line in geometry["coordinates"]:
            coords.extend(line)
    elif geom_type == "MultiPolygon":
        for polygon in geometry["coordinates"]:
            for line in polygon:
                coords.extend(line)
    elif geom_type == "GeometryCollection":
        for geom in geometry["geometries"]:
            coords.extend(extract_coords_from_geometry(geom))

    return coords

def get_bounding_box(geojson_data: Dict) -> Tuple[float, float, float, float]:
    """
    Extract the bounding box (west, south, east, north) from a GeoJSON object.

    Args:
        geojson_data: A GeoJSON object (loaded as a Python dictionary)

    Returns:
        Tuple of (west, south, east, north) coordinates
    """
    # Check if the GeoJSON already has a bbox property
    if "bbox" in geojson_data:
        bbox = geojson_data["bbox"]
        # GeoJSON bbox format is [west, south, east, north]
        return (bbox[0], bbox[1], bbox[2], bbox[3])

    # If no bbox, calculate it ourselves
    all_coords = []

    if geojson_data["type"] == "Feature":
        all_coords.extend(extract_coords_from_geometry(geojson_data["geometry"]))
    elif geojson_data["type"] == "FeatureCollection":
        for feature in geojson_data["features"]:
            all_coords.extend(extract_coords_from_geometry(feature["geometry"]))
    else:
        # Assume it's a geometry object
        all_coords.extend(extract_coords_from_geometry(geojson_data))

    if not all_coords:
        raise ValueError("No coordinates found in the GeoJSON data")

    # Extract longitudes (x) and latitudes (y) - IMPORTANT: GeoJSON stores [lon, lat]
    lons = [coord[0] for coord in all_coords]  # Longitude is first
    lats = [coord[1] for coord in all_coords]  # Latitude is second

    # Calculate bounds
    west = min(lons)
    east = max(lons)
    south = min(lats)
    north = max(lats)

    return (west, south, east, north)

def load_json_with_encoding(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file with appropriate encoding detection.

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON data as a dictionary

    Raises:
        ValueError: If the file cannot be parsed as JSON with any encoding
    """
    encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                data = json.load(f)
                logging.debug(f"Successfully loaded JSON file with {encoding} encoding")
                return data
        except UnicodeDecodeError:
            continue
        except json.JSONDecodeError:
            continue
        except Exception as e:
            continue

    # If we get here, none of the encodings worked
    raise ValueError(
        f"Could not load {file_path} as valid JSON with any common encoding"
    )

def is_valid_geojson(json_data: Dict[str, Any]) -> bool:
    """
    Check if the provided JSON data is valid GeoJSON.

    Args:
        json_data: Parsed JSON data

    Returns:
        True if it's valid GeoJSON, False otherwise
    """
    # Check if it's a dictionary
    if not isinstance(json_data, dict):
        return False

    # Basic GeoJSON structure check
    if "type" not in json_data:
        return False

    # Valid GeoJSON types
    valid_types = [
        "FeatureCollection",
        "Feature",
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
        "GeometryCollection",
    ]

    if json_data["type"] not in valid_types:
        return False

    # More specific checks based on type
    if json_data["type"] == "FeatureCollection":
        return "features" in json_data and isinstance(json_data["features"], list)

    elif json_data["type"] == "Feature":
        return "geometry" in json_data and isinstance(json_data["geometry"], dict)

    # For geometry types, check for coordinates
    elif json_data["type"] in [
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
    ]:
        return "coordinates" in json_data

    # For GeometryCollection
    elif json_data["type"] == "GeometryCollection":
        return "geometries" in json_data and isinstance(json_data["geometries"], list)

    return False

def convert_to_geojson(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert various JSON formats to valid GeoJSON.

    This function tries to intelligently convert different JSON structures
    to proper GeoJSON format based on the content.

    Args:
        json_data: The parsed JSON data

    Returns:
        A valid GeoJSON dictionary

    Raises:
        ValueError: If the JSON cannot be converted to GeoJSON
    """
    # Case 1: It's already GeoJSON but failed validation due to minor issues
    if "type" in json_data:
        if json_data["type"] in ["Feature", "FeatureCollection"]:
            # Try to fix common issues
            if json_data["type"] == "FeatureCollection" and "features" not in json_data:
                json_data["features"] = []

            if json_data["type"] == "Feature" and "geometry" not in json_data:
                raise ValueError(
                    "Feature missing geometry and cannot be automatically fixed"
                )

            return json_data

    # Case 2: It contains coordinates or a bounding box directly
    if "coordinates" in json_data:
        # Assume it's meant to be a Polygon
        return {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": json_data["coordinates"]},
            "properties": {},
        }

    # Case 3: It contains a bounding box specified as [west, south, east, north]
    if (
        "bbox" in json_data
        and isinstance(json_data["bbox"], list)
        and len(json_data["bbox"]) >= 4
    ):
        west, south, east, north = json_data["bbox"][0:4]
        return create_geojson_from_bbox(west, south, east, north)

    # Case 4: It contains explicit lat/lon boundaries
    keys = [k.lower() for k in json_data.keys()]
    if all(k in keys for k in ["north", "south", "east", "west"]):
        idx = {k: keys.index(k) for k in ["north", "south", "east", "west"]}
        actual_keys = list(json_data.keys())
        north = json_data[actual_keys[idx["north"]]]
        south = json_data[actual_keys[idx["south"]]]
        east = json_data[actual_keys[idx["east"]]]
        west = json_data[actual_keys[idx["west"]]]
        return create_geojson_from_bbox(west, south, east, north)

    # If we've gotten here, we can't automatically convert it
    raise ValueError("Cannot automatically convert the provided JSON to GeoJSON format")

def create_geojson_from_bbox(
    west: float, south: float, east: float, north: float
) -> Dict[str, Any]:
    """
    Create a GeoJSON polygon from bounding box coordinates.

    Args:
        west: Western longitude
        south: Southern latitude
        east: Eastern longitude
        north: Northern latitude

    Returns:
        A GeoJSON Feature with a Polygon geometry
    """
    # Create a polygon from the bounding box
    coordinates = [
        [
            [west, south],  # Bottom-left
            [east, south],  # Bottom-right
            [east, north],  # Top-right
            [west, north],  # Top-left
            [west, south],  # Close the polygon
        ]
    ]

    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": coordinates},
        "properties": {
            "description": f"Bounding box: N:{north}, W:{west}, S:{south}, E:{east}"
        },
    }

def create_temp_geojson(geojson_data: Dict[str, Any], request_id: str) -> str:
    """
    Create a temporary GeoJSON file with the provided data.

    Args:
        geojson_data: Valid GeoJSON data
        request_id: Unique identifier for the request (used in filename)

    Returns:
        Path to the created temporary file
    """
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"{request_id}_temp_geojson.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=2)

    return output_path
