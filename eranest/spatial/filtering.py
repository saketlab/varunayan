"""
Optimized spatial filtering operations for large datasets.

This module provides high-performance spatial filtering capabilities
with memory-efficient algorithms and parallel processing support.
"""

import logging
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

from ..constants import (
    DEFAULT_PARALLEL_WORKERS,
    SPATIAL_FILTER_CHUNK_SIZE,
    USE_SPATIAL_INDEX,
)
from ..exceptions import DataProcessingError, GeospatialError
from .geometry import merge_geometries, validate_coordinates

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    """Result of spatial filtering operation."""

    filtered_data: pd.DataFrame
    total_points: int
    filtered_points: int
    processing_time: float
    inside_percentage: float

    def __post_init__(self):
        """Calculate derived metrics."""
        if self.total_points > 0:
            self.inside_percentage = (self.filtered_points / self.total_points) * 100
        else:
            self.inside_percentage = 0.0


class SpatialFilter:
    """
    High-performance spatial filtering with optimizations for large datasets.

    This class provides memory-efficient and fast spatial filtering operations
    with support for chunked processing and parallel execution.
    """

    def __init__(
        self,
        chunk_size: int = SPATIAL_FILTER_CHUNK_SIZE,
        use_spatial_index: bool = USE_SPATIAL_INDEX,
        parallel_processing: bool = False,
        max_workers: int = DEFAULT_PARALLEL_WORKERS,
        memory_limit_mb: int = 2048,
    ):
        """
        Initialize the spatial filter.

        Args:
            chunk_size: Number of points to process in each chunk
            use_spatial_index: Whether to use spatial indexing for acceleration
            parallel_processing: Enable parallel processing for large datasets
            max_workers: Maximum number of parallel workers
            memory_limit_mb: Memory limit for processing in MB
        """
        self.chunk_size = chunk_size
        self.use_spatial_index = use_spatial_index
        self.parallel_processing = parallel_processing
        self.max_workers = max_workers
        self.memory_limit_mb = memory_limit_mb

        self._spatial_index = None
        self._geometry_cache = {}

    def filter_dataset(
        self,
        dataset: xr.Dataset,
        geometry: Union[Dict[str, Any], Polygon, MultiPolygon],
        lat_coord: str = "latitude",
        lon_coord: str = "longitude",
    ) -> FilterResult:
        """
        Filter xarray Dataset by geometry with optimizations.

        Args:
            dataset: xarray Dataset to filter
            geometry: Geometry to filter by (GeoJSON dict or Shapely geometry)
            lat_coord: Name of latitude coordinate
            lon_coord: Name of longitude coordinate

        Returns:
            FilterResult with filtered data and metrics
        """
        start_time = time.time()

        logger.info("Starting optimized spatial filtering...")

        # Convert to shapely geometry if needed
        if isinstance(geometry, dict):
            shapely_geom = self._geojson_to_shapely(geometry)
        else:
            shapely_geom = geometry

        # Get coordinate arrays
        try:
            lats = dataset.coords[lat_coord].values
            lons = dataset.coords[lon_coord].values
        except KeyError as e:
            raise DataProcessingError(f"Coordinate not found in dataset: {e}")

        # Create coordinate grid
        lon_grid, lat_grid = np.meshgrid(lons, lats)

        # Pre-filter using bounding box for efficiency
        bbox_mask = self._create_bbox_mask(lat_grid, lon_grid, shapely_geom.bounds)

        if not np.any(bbox_mask):
            logger.warning("No points found within geometry bounding box")
            return FilterResult(
                filtered_data=pd.DataFrame(),
                total_points=lat_grid.size,
                filtered_points=0,
                processing_time=time.time() - start_time,
                inside_percentage=0.0,
            )

        # Get candidate points within bounding box
        candidate_lats = lat_grid[bbox_mask]
        candidate_lons = lon_grid[bbox_mask]

        logger.info(
            f"Pre-filtered to {len(candidate_lats)} candidate points using bounding box"
        )

        # Perform precise geometric filtering
        inside_mask = self._filter_points_by_geometry(
            candidate_lats, candidate_lons, shapely_geom
        )

        # Get final coordinate pairs
        final_lats = candidate_lats[inside_mask]
        final_lons = candidate_lons[inside_mask]

        logger.info(f"Final filtering result: {len(final_lats)} points inside geometry")

        # Convert dataset to DataFrame for filtered points
        filtered_df = self._extract_data_for_coordinates(
            dataset, final_lats, final_lons, lat_coord, lon_coord
        )

        processing_time = time.time() - start_time

        result = FilterResult(
            filtered_data=filtered_df,
            total_points=lat_grid.size,
            filtered_points=len(final_lats),
            processing_time=processing_time,
            inside_percentage=(len(final_lats) / lat_grid.size) * 100,
        )

        logger.info(f"Spatial filtering completed in {processing_time:.2f}s")
        logger.info(
            f"Filtered {result.filtered_points}/{result.total_points} points ({result.inside_percentage:.1f}%)"
        )

        return result

    def filter_dataframe(
        self,
        df: pd.DataFrame,
        geometry: Union[Dict[str, Any], Polygon, MultiPolygon],
        lat_col: str = "latitude",
        lon_col: str = "longitude",
    ) -> FilterResult:
        """
        Filter pandas DataFrame by geometry with optimizations.

        Args:
            df: pandas DataFrame to filter
            geometry: Geometry to filter by
            lat_col: Name of latitude column
            lon_col: Name of longitude column

        Returns:
            FilterResult with filtered data and metrics
        """
        start_time = time.time()

        # Convert to shapely geometry if needed
        if isinstance(geometry, dict):
            shapely_geom = self._geojson_to_shapely(geometry)
        else:
            shapely_geom = geometry

        # Validate columns
        if lat_col not in df.columns or lon_col not in df.columns:
            raise DataProcessingError(
                f"Required columns not found: {lat_col}, {lon_col}"
            )

        total_points = len(df)

        # Pre-filter using bounding box
        bbox_filtered = self._bbox_filter_dataframe(
            df, shapely_geom.bounds, lat_col, lon_col
        )

        if bbox_filtered.empty:
            return FilterResult(
                filtered_data=pd.DataFrame(),
                total_points=total_points,
                filtered_points=0,
                processing_time=time.time() - start_time,
                inside_percentage=0.0,
            )

        # Precise geometric filtering
        inside_mask = self._filter_points_by_geometry(
            bbox_filtered[lat_col].values, bbox_filtered[lon_col].values, shapely_geom
        )

        filtered_df = bbox_filtered[inside_mask].copy()

        processing_time = time.time() - start_time

        return FilterResult(
            filtered_data=filtered_df,
            total_points=total_points,
            filtered_points=len(filtered_df),
            processing_time=processing_time,
            inside_percentage=(len(filtered_df) / total_points) * 100,
        )

    def _geojson_to_shapely(
        self, geojson: Dict[str, Any]
    ) -> Union[Polygon, MultiPolygon]:
        """Convert GeoJSON to Shapely geometry with caching."""
        # Create cache key
        cache_key = str(hash(str(geojson)))

        if cache_key in self._geometry_cache:
            return self._geometry_cache[cache_key]

        # Convert GeoJSON to GeoDataFrame
        if geojson.get("type") == "FeatureCollection":
            gdf = gpd.GeoDataFrame.from_features(geojson["features"])
        elif geojson.get("type") == "Feature":
            gdf = gpd.GeoDataFrame.from_features([geojson])
        else:
            # Assume it's a geometry
            gdf = gpd.GeoDataFrame([1], geometry=[geojson], crs="EPSG:4326")

        # Ensure CRS is set
        if gdf.crs is None:
            gdf.crs = "EPSG:4326"

        # Merge all geometries into one
        unified_geom = merge_geometries(gdf.geometry.tolist())

        # Cache the result
        self._geometry_cache[cache_key] = unified_geom

        return unified_geom

    def _create_bbox_mask(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        bounds: Tuple[float, float, float, float],
    ) -> np.ndarray:
        """Create boolean mask for bounding box filtering."""
        minx, miny, maxx, maxy = bounds

        # Create mask
        lat_mask = (lat_grid >= miny) & (lat_grid <= maxy)
        lon_mask = (lon_grid >= minx) & (lon_grid <= maxx)

        return lat_mask & lon_mask

    def _bbox_filter_dataframe(
        self,
        df: pd.DataFrame,
        bounds: Tuple[float, float, float, float],
        lat_col: str,
        lon_col: str,
    ) -> pd.DataFrame:
        """Filter DataFrame by bounding box."""
        minx, miny, maxx, maxy = bounds

        mask = (
            (df[lat_col] >= miny)
            & (df[lat_col] <= maxy)
            & (df[lon_col] >= minx)
            & (df[lon_col] <= maxx)
        )

        return df[mask]

    def _filter_points_by_geometry(
        self, lats: np.ndarray, lons: np.ndarray, geometry: Union[Polygon, MultiPolygon]
    ) -> np.ndarray:
        """
        Filter coordinate points by geometry with optimizations.

        Args:
            lats: Array of latitude values
            lons: Array of longitude values
            geometry: Shapely geometry to filter by

        Returns:
            Boolean mask indicating points inside geometry
        """
        n_points = len(lats)

        # For small datasets, use simple approach
        if n_points <= self.chunk_size:
            return self._filter_points_simple(lats, lons, geometry)

        # For large datasets, use chunked processing
        if self.parallel_processing and n_points > self.chunk_size * 2:
            return self._filter_points_parallel(lats, lons, geometry)
        else:
            return self._filter_points_chunked(lats, lons, geometry)

    def _filter_points_simple(
        self, lats: np.ndarray, lons: np.ndarray, geometry: Union[Polygon, MultiPolygon]
    ) -> np.ndarray:
        """Simple point-in-polygon filtering."""
        points = [Point(lon, lat) for lon, lat in zip(lons, lats)]

        if self.use_spatial_index and len(points) > 100:
            # Use spatial index for medium-sized datasets
            return self._filter_with_spatial_index(points, geometry)
        else:
            # Direct filtering for small datasets
            return np.array([geometry.contains(point) for point in points])

    def _filter_points_chunked(
        self, lats: np.ndarray, lons: np.ndarray, geometry: Union[Polygon, MultiPolygon]
    ) -> np.ndarray:
        """Chunked point-in-polygon filtering."""
        n_points = len(lats)
        result_mask = np.zeros(n_points, dtype=bool)

        for i in range(0, n_points, self.chunk_size):
            end_idx = min(i + self.chunk_size, n_points)

            chunk_lats = lats[i:end_idx]
            chunk_lons = lons[i:end_idx]

            chunk_mask = self._filter_points_simple(chunk_lats, chunk_lons, geometry)
            result_mask[i:end_idx] = chunk_mask

        return result_mask

    def _filter_points_parallel(
        self, lats: np.ndarray, lons: np.ndarray, geometry: Union[Polygon, MultiPolygon]
    ) -> np.ndarray:
        """Parallel point-in-polygon filtering."""
        n_points = len(lats)
        result_mask = np.zeros(n_points, dtype=bool)

        # Create chunks for parallel processing
        chunk_indices = list(range(0, n_points, self.chunk_size))

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []

            for i in chunk_indices:
                end_idx = min(i + self.chunk_size, n_points)
                chunk_lats = lats[i:end_idx]
                chunk_lons = lons[i:end_idx]

                future = executor.submit(
                    self._filter_points_simple, chunk_lats, chunk_lons, geometry
                )
                futures.append((i, end_idx, future))

            # Collect results
            for i, end_idx, future in futures:
                chunk_mask = future.result()
                result_mask[i:end_idx] = chunk_mask

        return result_mask

    def _filter_with_spatial_index(
        self, points: List[Point], geometry: Union[Polygon, MultiPolygon]
    ) -> np.ndarray:
        """Use spatial index for efficient filtering."""
        # Build spatial index
        tree = STRtree(points)

        # Query index for potential matches
        potential_indices = tree.query(geometry)

        # Create result mask
        result_mask = np.zeros(len(points), dtype=bool)

        # Check precise containment for potential matches
        for idx in potential_indices:
            if geometry.contains(points[idx]):
                result_mask[idx] = True

        return result_mask

    def _extract_data_for_coordinates(
        self,
        dataset: xr.Dataset,
        lats: np.ndarray,
        lons: np.ndarray,
        lat_coord: str,
        lon_coord: str,
    ) -> pd.DataFrame:
        """Extract dataset values for specific coordinates efficiently."""
        # Convert dataset to DataFrame
        df = dataset.to_dataframe().reset_index()

        # Create coordinate lookup
        coord_pairs = set(zip(lats, lons))

        # Filter DataFrame
        mask = df.apply(
            lambda row: (row[lat_coord], row[lon_coord]) in coord_pairs, axis=1
        )

        return df[mask].copy()


# Convenience functions


def filter_by_geometry(
    data: Union[xr.Dataset, pd.DataFrame],
    geometry: Union[Dict[str, Any], Polygon, MultiPolygon],
    lat_coord: str = "latitude",
    lon_coord: str = "longitude",
    **kwargs,
) -> FilterResult:
    """
    Filter data by geometry using optimized spatial operations.

    Args:
        data: Dataset or DataFrame to filter
        geometry: Geometry to filter by
        lat_coord: Name of latitude coordinate/column
        lon_coord: Name of longitude coordinate/column
        **kwargs: Additional arguments for SpatialFilter

    Returns:
        FilterResult with filtered data and metrics
    """
    filter_instance = SpatialFilter(**kwargs)

    if isinstance(data, xr.Dataset):
        return filter_instance.filter_dataset(data, geometry, lat_coord, lon_coord)
    elif isinstance(data, pd.DataFrame):
        return filter_instance.filter_dataframe(data, geometry, lat_coord, lon_coord)
    else:
        raise DataProcessingError(f"Unsupported data type: {type(data)}")


def optimize_spatial_filtering(
    geometry: Union[Dict[str, Any], Polygon, MultiPolygon], tolerance: float = 0.01
) -> Union[Polygon, MultiPolygon]:
    """
    Optimize geometry for spatial filtering operations.

    Args:
        geometry: Geometry to optimize
        tolerance: Simplification tolerance

    Returns:
        Optimized geometry
    """
    if isinstance(geometry, dict):
        # Convert GeoJSON to Shapely
        gdf = gpd.GeoDataFrame.from_features(
            [geometry] if geometry.get("type") == "Feature" else geometry["features"]
        )
        shapely_geom = merge_geometries(gdf.geometry.tolist())
    else:
        shapely_geom = geometry

    # Simplify geometry
    simplified = shapely_geom.simplify(tolerance, preserve_topology=True)

    # Remove small holes and islands
    if hasattr(simplified, "geoms"):
        # MultiPolygon
        large_geoms = [
            geom for geom in simplified.geoms if geom.area > tolerance * tolerance
        ]
        if large_geoms:
            simplified = merge_geometries(large_geoms)

    return simplified
