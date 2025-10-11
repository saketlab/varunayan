import datetime as dt
import logging
from typing import Any, Dict, List, Optional, Union, cast

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from ..util.logging_utils import get_logger

logger = get_logger(level=logging.DEBUG)


def set_v_data_fil(verbosity: int) -> None:

    if verbosity == 0:
        logger.setLevel(logging.WARNING)

    elif verbosity == 1:
        logger.setLevel(logging.INFO)

    elif verbosity == 2:
        logger.setLevel(logging.DEBUG)

    else:
        logger.setLevel(logging.WARNING)


# pyright: reportUnknownMemberType=false
def filter_netcdf_by_shapefile(
    ds: xr.Dataset,
    geojson_data: Union[Dict[str, Any], gpd.GeoDataFrame],
    dist_features: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Filter a NetCDF dataset to only include grid points that fall within the GeoJSON polygon(s).
    Internally handles multi-feature GeoJSONs by matching points to each feature individually,
    then taking the union of all matched points.

    Parameters:
        ds: xarray Dataset
        geojson_data: Loaded GeoJSON (as dict or GeoDataFrame)
        dist_features: List of attribute/property names in the GeoJSON to use as composite feature identifier

    Returns:
        A pandas DataFrame with filtered points and feature identification.
    """
    import warnings

    from shapely.validation import make_valid

    logger.info("Starting filtering process...")
    start_time = dt.datetime.now()

    # Step 0: Convert GeoJSON to GeoDataFrame
    if isinstance(geojson_data, dict):
        features = geojson_data.get("features", [geojson_data])
        gdf: gpd.GeoDataFrame = gpd.GeoDataFrame.from_features(features)
    else:
        gdf = geojson_data.copy()

    if gdf.crs is None:
        gdf.crs = "EPSG:4326"

    num_features = len(gdf)
    logger.info(f"✓ GeoJSON contains {num_features} feature(s)")

    # Check if all dist_features exist in the GeoDataFrame
    if dist_features:
        missing_features = [feat for feat in dist_features if feat not in gdf.columns]
        if missing_features:
            logger.warning(
                f"Features {missing_features} not found in GeoJSON. Available columns: {list(gdf.columns)}"
            )
            # Remove missing features from the list
            dist_features = [feat for feat in dist_features if feat in gdf.columns]
            if not dist_features:
                logger.warning(
                    "No valid feature columns found. Proceeding without feature identification."
                )
                dist_features = None

    # Step 1: Extract all lat/lon combinations
    logger.info("→ Extracting unique lat/lon coordinates from dataset...")

    lat_coord = "latitude" if "latitude" in ds.coords else "lat"
    lon_coord = "longitude" if "longitude" in ds.coords else "lon"
    lats = np.asarray(ds.coords[lat_coord].values)
    lons = np.asarray(ds.coords[lon_coord].values)

    lon_grid, lat_grid = np.meshgrid(lons, lats)
    unique_coords = pd.DataFrame(
        {"latitude": lat_grid.flatten(), "longitude": lon_grid.flatten()}
    ).drop_duplicates()

    total_points = len(unique_coords)
    logger.info(f"✓ Found {total_points} unique lat/lon combinations")

    # Add geometry column
    unique_coords["geometry"] = [
        Point(lon, lat)
        for lon, lat in zip(unique_coords["longitude"], unique_coords["latitude"])
    ]
    gdf_points = gpd.GeoDataFrame(unique_coords, geometry="geometry", crs="EPSG:4326")

    # Step 1.5: Comprehensive geometry validation and repair
    logger.info("→ Validating and repairing geometries...")

    # First check for invalid geometries
    invalid_mask = ~gdf.is_valid
    invalid_count = invalid_mask.sum()

    if invalid_count > 0:
        logger.warning(
            f"Found {invalid_count} invalid geometries. Attempting repair..."
        )

        # Try multiple repair strategies
        for idx in gdf[invalid_mask].index:
            original_geom = cast(BaseGeometry, gdf.loc[idx, "geometry"])

            # Strategy 1: buffer(0) - fixes self-intersections and other topology issues
            try:
                buffered = original_geom.buffer(0)
                if buffered.is_valid and not buffered.is_empty:
                    gdf.loc[idx, "geometry"] = buffered
                    continue
            except Exception as e:
                logger.debug(f"Buffer(0) failed for feature {idx}: {e}")

            # Strategy 2: make_valid() - Shapely's built-in repair function
            try:
                repaired = make_valid(original_geom)
                if repaired.is_valid and not repaired.is_empty:
                    gdf.loc[idx, "geometry"] = repaired
                    continue
            except Exception as e:
                logger.debug(f"make_valid() failed for feature {idx}: {e}")

            # Strategy 3: Small buffer operation
            try:
                small_buffer = original_geom.buffer(1e-10).buffer(-1e-10)
                if small_buffer.is_valid and not small_buffer.is_empty:
                    gdf.loc[idx, "geometry"] = small_buffer
                    continue
            except Exception as e:
                logger.debug(f"Small buffer operation failed for feature {idx}: {e}")

            # If all repair strategies fail, log and mark for removal
            logger.warning(
                f"Could not repair geometry for feature {idx}. Will be excluded."
            )

    # Remove any remaining invalid or empty geometries
    original_count = len(gdf)
    gdf = gdf[gdf.is_valid & ~gdf.is_empty]
    removed_count = original_count - len(gdf)

    if removed_count > 0:
        logger.warning(f"Removed {removed_count} invalid/empty geometries")

    logger.info(f"✓ {len(gdf)} valid features retained after geometry validation")

    if gdf.empty:
        raise ValueError(
            "All features in the GeoJSON were invalid and could not be fixed."
        )

    # Step 2: Filtering with error handling and feature identification
    logger.info("→ Filtering coordinates by feature geometries...")
    filter_start = dt.datetime.now()
    matched_list: List[gpd.GeoDataFrame] = []

    for idx, feature in gdf.iterrows():
        try:
            geom = cast(BaseGeometry, feature.geometry)

            # Additional validation before intersection
            if not geom.is_valid or geom.is_empty:
                logger.warning(f"Skipping invalid/empty geometry for feature {idx}")
                continue

            # Perform intersection with error handling
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                points_in_geom = gdf_points[gdf_points.geometry.intersects(geom)].copy()

            if not points_in_geom.empty:
                # Create composite feature identifier from multiple attributes
                if dist_features:
                    # Create composite key by combining values with separator
                    feature_values = []
                    for feat_name in dist_features:
                        feat_value = feature[feat_name]
                        # Handle None/NaN values
                        if pd.isna(feat_value):
                            feat_value = "None"
                        feature_values.append(str(feat_value))

                    # Join with a separator (you can customize this)
                    composite_key = "_".join(feature_values)
                    points_in_geom["feature"] = composite_key

                    # Optionally, also add individual feature columns for easier access
                    for feat_name in dist_features:
                        points_in_geom[feat_name] = feature[feat_name]
                else:
                    feature_name = f"feature_{idx}"
                    points_in_geom["feature"] = feature_name

                matched_list.append(points_in_geom)

                if dist_features:
                    logger.debug(
                        f"Feature {idx} ({composite_key}): {len(points_in_geom)} points matched"
                    )
                else:
                    logger.debug(
                        f"Feature {idx} (feature_{idx}): {len(points_in_geom)} points matched"
                    )

        except Exception as e:
            logger.error(f"Error processing feature {idx}: {e}")
            logger.warning(f"Skipping feature {idx} due to geometry error")
            continue

    # Concatenate all matched DataFrames at once
    if matched_list:
        matched = pd.concat(matched_list, ignore_index=True)
        # For points that belong to multiple features, keep all associations
        # (don't drop duplicates based on lat/lon since we want feature info)
        logger.info(f"✓ Found points in {len(matched_list)} features")
    else:
        # Create empty GeoDataFrame with same structure
        base_columns = list(gdf_points.columns) + ["feature"]
        if dist_features:
            base_columns.extend(dist_features)
        matched = gpd.GeoDataFrame(
            columns=base_columns,
            geometry="geometry",
            crs="EPSG:4326",
        )
    filter_time = dt.datetime.now() - filter_start

    logger.info(
        f"✓ Spatial filtering done in {filter_time.total_seconds():.2f} seconds"
    )
    logger.info(f"✓ Total matched points: {len(matched)}")

    if matched.empty:
        raise ValueError("No points found inside any features in the GeoJSON.")

    # Step 3: Join with original dataset
    df = ds.to_dataframe().reset_index()
    lat_col = "latitude" if "latitude" in df.columns else "lat"
    lon_col = "longitude" if "longitude" in df.columns else "lon"

    # Merge using lat/lon
    logger.info("→ Merging matched points with dataset values...")

    if dist_features:
        # Include feature column and individual feature columns in merge
        merge_columns = ["latitude", "longitude", "feature"] + dist_features
        final_df = pd.merge(
            matched[merge_columns],
            df,
            left_on=["latitude", "longitude"],
            right_on=[lat_col, lon_col],
            how="inner",
        )
    else:
        # Original behavior - no feature column
        final_df = pd.merge(
            matched[["latitude", "longitude", "feature"]],
            df,
            left_on=["latitude", "longitude"],
            right_on=[lat_col, lon_col],
            how="inner",
        )

    logger.info("✓ Merge complete")
    logger.info(f"→ Final dataset shape: {final_df.shape}")

    # Log some info about the composite keys if used
    if dist_features and not final_df.empty:
        unique_composites = final_df["feature"].nunique()
        logger.info(f"✓ Found {unique_composites} unique composite feature identifiers")
        logger.debug(
            f"Sample composite keys: {final_df['feature'].unique()[:5].tolist()}"
        )

    logger.info(
        f"✓ Total processing time: {(dt.datetime.now() - start_time).total_seconds():.2f} seconds"
    )

    return final_df


def get_unique_coordinates_in_polygon(
    ds: xr.Dataset, geojson_data: Union[Dict[str, Any], gpd.GeoDataFrame]
) -> pd.DataFrame:
    """
    Alternative helper function that returns just the unique lat/lon pairs inside the polygon.
    This can be useful for other operations or caching coordinate filtering results.
    """
    logger.debug("Extracting unique coordinates inside polygon...")

    # Convert GeoJSON to GeoDataFrame
    if isinstance(geojson_data, dict):
        gdf = gpd.GeoDataFrame.from_features(
            geojson_data["features"] if "features" in geojson_data else [geojson_data]
        )
    else:
        gdf = geojson_data.copy()

    if gdf.crs is None:
        gdf.crs = "EPSG:4326"

    unified_polygon = gdf.geometry.union_all()

    # Get coordinate arrays
    lat_coord = "latitude" if "latitude" in ds.coords else "lat"
    lon_coord = "longitude" if "longitude" in ds.coords else "lon"
    lats = np.asarray(ds.coords[lat_coord].values)
    lons = np.asarray(ds.coords[lon_coord].values)

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

    subset = inside_coords[["latitude", "longitude"]].copy()
    return pd.DataFrame(subset)
