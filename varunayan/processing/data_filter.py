import datetime as dt
import logging
from typing import Dict

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import Point

from ..util.logging_utils import get_logger

logger = get_logger(level=logging.INFO)


def filter_netcdf_by_shapefile(ds: xr.Dataset, geojson_data: Dict) -> pd.DataFrame:
    """
    Filter a NetCDF dataset to only include grid points that fall within the GeoJSON polygon
    by first identifying unique lat/lon pairs that are inside the polygon, then filtering the dataset.
    This is much more efficient than converting the entire dataset to DataFrame first.
    """
    logger.info("Starting optimized filtering process...")
    start_time = dt.datetime.now()

    # Convert GeoJSON to GeoDataFrame for efficient spatial operations
    if isinstance(geojson_data, dict):
        gdf = gpd.GeoDataFrame.from_features(
            geojson_data["features"] if "features" in geojson_data else [geojson_data]
        )
    else:
        gdf = geojson_data

    # Make sure the CRS is set
    if gdf.crs is None:
        gdf.crs = "EPSG:4326"  # WGS84 - standard for geographic coordinates

    # Create a unified geometry from all polygons in the GeoDataFrame
    unified_polygon = gdf.geometry.union_all()

    # Step 1: Extract unique lat/lon coordinates from the NetCDF dataset
    logger.info("→ Extracting unique lat/lon coordinates from dataset...")

    # Get the coordinate arrays
    lats = (
        ds.coords["latitude"].values
        if "latitude" in ds.coords
        else ds.coords["lat"].values
    )
    lons = (
        ds.coords["longitude"].values
        if "longitude" in ds.coords
        else ds.coords["lon"].values
    )

    # Create all possible lat/lon combinations (grid points)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    unique_coords = pd.DataFrame(
        {"latitude": lat_grid.flatten(), "longitude": lon_grid.flatten()}
    ).drop_duplicates()

    total_unique_points = len(unique_coords)
    logger.info(f"✓ Found {total_unique_points} unique lat/lon combinations")

    # Step 2: Filter unique coordinates to find which ones are inside the polygon
    logger.info("→ Filtering unique coordinates against polygon...")
    filter_start = dt.datetime.now()

    # Create Point geometries for unique coordinates
    unique_coords["geometry"] = [
        Point(lon, lat)
        for lon, lat in zip(unique_coords["longitude"], unique_coords["latitude"])
    ]

    # Convert to GeoDataFrame
    gdf_unique_points = gpd.GeoDataFrame(
        unique_coords, geometry="geometry", crs="EPSG:4326"
    )

    # Filter points that are within the polygon
    inside_coords = gdf_unique_points[
        gdf_unique_points.geometry.intersects(unified_polygon)
    ].copy()

    # Drop the geometry column and keep only lat/lon
    inside_coords = inside_coords[["latitude", "longitude"]].copy()

    filter_time = dt.datetime.now() - filter_start
    points_inside_count = len(inside_coords)
    points_outside_count = total_unique_points - points_inside_count

    logger.info(
        f"✓ Coordinate filtering completed in {filter_time.total_seconds():.2f} seconds"
    )
    logger.info(f"  - Points inside: {points_inside_count}")
    logger.info(f"  - Points outside: {points_outside_count}")
    logger.info(
        f"  - Percentage inside: {points_inside_count/total_unique_points*100:.2f}%"
    )

    # Verify we found points inside
    if points_inside_count == 0:
        logger.warning("\n!!! WARNING: No points found inside the shapefile !!!")
        logger.warning("Possible reasons:")
        logger.warning(
            "1. The selected variable may not have valid values in the specified region."
        )
        logger.warning(
            "2. The region is too small or falls outside the spatial coverage of the dataset."
        )
        logger.warning(
            "3. All dataset grid points fall outside the shapefile boundaries."
        )

        # Additional debugging info
        logger.info("\nDataset coordinate ranges:")
        logger.info(f"  Latitude: {lats.min():.4f} to {lats.max():.4f}")
        logger.info(f"  Longitude: {lons.min():.4f} to {lons.max():.4f}")

        # Print shapefile bounds
        logger.info("\nShapefile bounds (west, south, east, north):")
        bounds = unified_polygon.bounds
        if isinstance(bounds, tuple):
            logger.info(
                f"  {bounds[0]:.4f}, {bounds[1]:.4f}, {bounds[2]:.4f}, {bounds[3]:.4f}"
            )
        else:
            logger.info(f"  {bounds}")

        raise ValueError("No points found inside the specified shapefile")

    # Step 3: Use the inside coordinates to filter the original dataset
    logger.info("→ Filtering original dataset using inside coordinates...")
    dataset_filter_start = dt.datetime.now()

    # First convert the dataset to DataFrame
    logger.info("  Converting dataset to DataFrame...")
    df = ds.to_dataframe().reset_index()
    original_rows = len(df)
    logger.info(f"  ✓ Converted to DataFrame with {original_rows} rows")

    # Create a set of (lat, lon) tuples for fast lookup
    inside_coord_tuples = set(
        zip(inside_coords["latitude"], inside_coords["longitude"])
    )
    logger.info(
        f"  ✓ Created lookup set with {len(inside_coord_tuples)} coordinate pairs"
    )

    # Filter the DataFrame to keep only rows where (lat, lon) pair is in the inside set
    logger.info("  Filtering DataFrame rows...")
    lat_col = "latitude" if "latitude" in df.columns else "lat"
    lon_col = "longitude" if "longitude" in df.columns else "lon"

    # Create a boolean mask for rows where the lat/lon combination is inside
    df["coord_pair"] = list(zip(df[lat_col], df[lon_col]))
    mask = df["coord_pair"].isin(inside_coord_tuples)

    # Apply the filter
    filtered_df = df[mask].copy()

    # Remove the temporary column
    filtered_df = filtered_df.drop(columns=["coord_pair"])

    filtered_rows = len(filtered_df)
    logger.info(f"  ✓ Filtered from {original_rows} to {filtered_rows} rows")

    dataset_filter_time = dt.datetime.now() - dataset_filter_start
    logger.info(
        f"✓ Dataset filtering completed in {dataset_filter_time.total_seconds():.2f} seconds"
    )

    end_time = dt.datetime.now()
    total_time = (end_time - start_time).total_seconds()

    logger.info("\n--- Final Filtering Results ---")
    logger.info(f"Total processing time: {total_time:.2f} seconds")
    logger.info(f"Final DataFrame shape: {filtered_df.shape}")
    logger.info(f"Rows in final dataset: {len(filtered_df)}")

    return filtered_df


def get_unique_coordinates_in_polygon(
    ds: xr.Dataset, geojson_data: Dict
) -> pd.DataFrame:
    """
    Alternative helper function that returns just the unique lat/lon pairs inside the polygon.
    This can be useful for other operations or caching coordinate filtering results.
    """
    logger.info("Extracting unique coordinates inside polygon...")

    # Convert GeoJSON to GeoDataFrame
    if isinstance(geojson_data, dict):
        gdf = gpd.GeoDataFrame.from_features(
            geojson_data["features"] if "features" in geojson_data else [geojson_data]
        )
    else:
        gdf = geojson_data

    if gdf.crs is None:
        gdf.crs = "EPSG:4326"

    unified_polygon = gdf.geometry.union_all()

    # Get coordinate arrays
    lats = (
        ds.coords["latitude"].values
        if "latitude" in ds.coords
        else ds.coords["lat"].values
    )
    lons = (
        ds.coords["longitude"].values
        if "longitude" in ds.coords
        else ds.coords["lon"].values
    )

    # Create grid and unique combinations
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    unique_coords = pd.DataFrame(
        {"latitude": lat_grid.flatten(), "longitude": lon_grid.flatten()}
    ).drop_duplicates()

    # Filter coordinates
    unique_coords["geometry"] = [
        Point(lon, lat)
        for lon, lat in zip(unique_coords["longitude"], unique_coords["latitude"])
    ]
    gdf_points = gpd.GeoDataFrame(unique_coords, geometry="geometry", crs="EPSG:4326")
    inside_coords = gdf_points[gdf_points.geometry.intersects(unified_polygon)]

    return inside_coords[["latitude", "longitude"]].copy()
