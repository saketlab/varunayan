"""
Spatial aggregation utilities for climate data.

This module provides functions for aggregating gridded climate data
to administrative boundaries or other polygons.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point


def aggregate_to_polygons(
    data: pd.DataFrame,
    polygons: gpd.GeoDataFrame,
    value_cols: Union[str, List[str]],
    method: str = "point_in_polygon",
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    polygon_id_col: Optional[str] = None,
    agg_func: str = "mean",
) -> gpd.GeoDataFrame:
    """
    Aggregate gridded data to polygon boundaries.

    Args:
        data: DataFrame with gridded climate data (must have lat/lon columns)
        polygons: GeoDataFrame with polygon geometries
        value_cols: Column name(s) containing values to aggregate
        method: Aggregation method:
            - 'point_in_polygon': Average all grid points within each polygon
            - 'nearest_centroid': Use value from grid point nearest to polygon centroid
        lat_col: Name of latitude column in data
        lon_col: Name of longitude column in data
        polygon_id_col: Column in polygons to use as identifier (default: index)
        agg_func: Aggregation function ('mean', 'sum', 'max', 'min', 'median')

    Returns:
        GeoDataFrame with aggregated values for each polygon
    """
    if isinstance(value_cols, str):
        value_cols = [value_cols]

    if polygon_id_col is None:
        polygons = polygons.copy()
        polygons["_polygon_id"] = polygons.index
        polygon_id_col = "_polygon_id"

    points = gpd.GeoDataFrame(
        data,
        geometry=gpd.points_from_xy(data[lon_col], data[lat_col]),
        crs="EPSG:4326",
    )

    if polygons.crs != "EPSG:4326":
        polygons = polygons.to_crs("EPSG:4326")

    if method == "point_in_polygon":
        joined = gpd.sjoin(points, polygons, how="inner", predicate="within")

        agg_dict = {col: agg_func for col in value_cols}
        aggregated = joined.groupby(polygon_id_col).agg(agg_dict).reset_index()

        result = polygons[[polygon_id_col, "geometry"]].merge(
            aggregated, on=polygon_id_col, how="left"
        )

    elif method == "nearest_centroid":
        centroids = polygons.copy()
        centroids["centroid"] = centroids.geometry.centroid

        results = []
        for idx, row in centroids.iterrows():
            centroid = row["centroid"]
            distances = np.sqrt(
                (points[lon_col] - centroid.x) ** 2
                + (points[lat_col] - centroid.y) ** 2
            )
            nearest_idx = distances.idxmin()
            nearest_values = {col: points.loc[nearest_idx, col] for col in value_cols}
            nearest_values[polygon_id_col] = row[polygon_id_col]
            results.append(nearest_values)

        aggregated = pd.DataFrame(results)
        result = polygons[[polygon_id_col, "geometry"]].merge(
            aggregated, on=polygon_id_col, how="left"
        )

    else:
        raise ValueError(
            f"Unknown method: {method}. Use 'point_in_polygon' or 'nearest_centroid'"
        )

    return gpd.GeoDataFrame(result, geometry="geometry", crs="EPSG:4326")


def check_grid_coverage(
    grid_data: pd.DataFrame,
    polygons: gpd.GeoDataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    polygon_id_col: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check how well the grid data covers the polygon boundaries.

    Args:
        grid_data: DataFrame with gridded climate data
        polygons: GeoDataFrame with polygon geometries
        lat_col: Name of latitude column
        lon_col: Name of longitude column
        polygon_id_col: Column to use as polygon identifier

    Returns:
        Dictionary with coverage statistics:
        - total_polygons: Number of polygons
        - covered_polygons: Number of polygons with at least one grid point
        - empty_polygons: Number of polygons with no grid points
        - coverage_percent: Percentage of polygons covered
        - points_per_polygon: DataFrame with point counts per polygon
        - uncovered_polygon_ids: List of polygon IDs with no coverage
    """
    if polygon_id_col is None:
        polygons = polygons.copy()
        polygons["_polygon_id"] = polygons.index
        polygon_id_col = "_polygon_id"

    unique_points = grid_data[[lat_col, lon_col]].drop_duplicates()
    points = gpd.GeoDataFrame(
        unique_points,
        geometry=gpd.points_from_xy(unique_points[lon_col], unique_points[lat_col]),
        crs="EPSG:4326",
    )

    if polygons.crs != "EPSG:4326":
        polygons = polygons.to_crs("EPSG:4326")

    joined = gpd.sjoin(points, polygons, how="right", predicate="within")

    points_per_polygon = (
        joined.groupby(polygon_id_col).size().reset_index(name="n_points")
    )

    all_polygons = polygons[[polygon_id_col]].copy()
    points_per_polygon = all_polygons.merge(
        points_per_polygon, on=polygon_id_col, how="left"
    )
    points_per_polygon["n_points"] = (
        points_per_polygon["n_points"].fillna(0).astype(int)
    )

    total = len(polygons)
    covered = (points_per_polygon["n_points"] > 0).sum()
    empty = total - covered

    uncovered = points_per_polygon[points_per_polygon["n_points"] == 0][
        polygon_id_col
    ].tolist()

    return {
        "total_polygons": total,
        "covered_polygons": int(covered),
        "empty_polygons": int(empty),
        "coverage_percent": round(100 * covered / total, 1) if total > 0 else 0,
        "points_per_polygon": points_per_polygon,
        "uncovered_polygon_ids": uncovered,
        "min_points": int(points_per_polygon["n_points"].min()),
        "max_points": int(points_per_polygon["n_points"].max()),
        "median_points": float(points_per_polygon["n_points"].median()),
    }


def visualize_grid_overlap(
    grid_data: pd.DataFrame,
    polygons: gpd.GeoDataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    output_file: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 10),
    title: str = "Grid Points and Polygon Boundaries",
) -> None:
    """
    Visualize the overlap between grid points and polygon boundaries.

    Args:
        grid_data: DataFrame with gridded climate data
        polygons: GeoDataFrame with polygon geometries
        lat_col: Name of latitude column
        lon_col: Name of longitude column
        output_file: Path to save the figure (optional)
        figsize: Figure size as (width, height)
        title: Plot title
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError(
            "matplotlib is required for visualization. Install with: pip install matplotlib"
        )

    unique_points = grid_data[[lat_col, lon_col]].drop_duplicates()
    points = gpd.GeoDataFrame(
        unique_points,
        geometry=gpd.points_from_xy(unique_points[lon_col], unique_points[lat_col]),
        crs="EPSG:4326",
    )

    if polygons.crs != "EPSG:4326":
        polygons = polygons.to_crs("EPSG:4326")

    fig, ax = plt.subplots(figsize=figsize)

    polygons.boundary.plot(ax=ax, color="black", linewidth=0.5)

    points.plot(ax=ax, color="red", markersize=5, alpha=0.6, label="Grid points")

    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend()

    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        print(f"Figure saved to: {output_file}")
    else:
        plt.show()

    plt.close()


def compare_grids(
    grids: Dict[str, pd.DataFrame],
    polygons: Optional[gpd.GeoDataFrame] = None,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    output_file: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 10),
    title: str = "Grid Comparison",
) -> None:
    """
    Compare multiple grids visually (e.g., ERA5 vs IMD).

    Args:
        grids: Dictionary mapping grid names to DataFrames
        polygons: Optional GeoDataFrame with polygon boundaries to overlay
        lat_col: Name of latitude column
        lon_col: Name of longitude column
        output_file: Path to save the figure (optional)
        figsize: Figure size as (width, height)
        title: Plot title
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError(
            "matplotlib is required for visualization. Install with: pip install matplotlib"
        )

    colors = ["red", "blue", "green", "orange", "purple", "cyan"]

    fig, ax = plt.subplots(figsize=figsize)

    if polygons is not None:
        if polygons.crs != "EPSG:4326":
            polygons = polygons.to_crs("EPSG:4326")
        polygons.boundary.plot(ax=ax, color="gray", linewidth=0.5, alpha=0.5)

    for i, (name, data) in enumerate(grids.items()):
        unique_points = data[[lat_col, lon_col]].drop_duplicates()
        color = colors[i % len(colors)]
        ax.scatter(
            unique_points[lon_col],
            unique_points[lat_col],
            c=color,
            s=10,
            alpha=0.6,
            label=f"{name} ({len(unique_points)} points)",
        )

    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend()

    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        print(f"Figure saved to: {output_file}")
    else:
        plt.show()

    plt.close()


def get_polygon_timeseries(
    data: pd.DataFrame,
    polygons: gpd.GeoDataFrame,
    value_col: str,
    time_col: str = "date",
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    polygon_id_col: Optional[str] = None,
    agg_func: str = "mean",
) -> pd.DataFrame:
    """
    Get time series of aggregated values for each polygon.

    Args:
        data: DataFrame with gridded climate data including time column
        polygons: GeoDataFrame with polygon geometries
        value_col: Column containing values to aggregate
        time_col: Column containing time/date values
        lat_col: Name of latitude column
        lon_col: Name of longitude column
        polygon_id_col: Column to use as polygon identifier
        agg_func: Aggregation function

    Returns:
        DataFrame with columns: polygon_id, time, aggregated_value
    """
    if polygon_id_col is None:
        polygons = polygons.copy()
        polygons["_polygon_id"] = polygons.index
        polygon_id_col = "_polygon_id"

    points = gpd.GeoDataFrame(
        data,
        geometry=gpd.points_from_xy(data[lon_col], data[lat_col]),
        crs="EPSG:4326",
    )

    if polygons.crs != "EPSG:4326":
        polygons = polygons.to_crs("EPSG:4326")

    joined = gpd.sjoin(
        points, polygons[[polygon_id_col, "geometry"]], how="inner", predicate="within"
    )

    aggregated = (
        joined.groupby([polygon_id_col, time_col])[value_col]
        .agg(agg_func)
        .reset_index()
    )

    aggregated.columns = pd.Index([polygon_id_col, time_col, value_col])

    return pd.DataFrame(aggregated)
