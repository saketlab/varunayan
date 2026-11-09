"""Shared download/filter helpers for gridded NetCDF modules."""

from __future__ import annotations

import gzip
import logging
import math
import os
from contextlib import contextmanager
from typing import IO, Any, Iterator, Optional, Union

import geopandas as gpd
import pandas as pd
import requests

logger = logging.getLogger(__name__)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(a))


@contextmanager
def atomic_open(
    path: Union[str, "os.PathLike[str]"], mode: str = "wb"
) -> Iterator[IO[Any]]:
    """Write beside path; path appears only if the whole block succeeds."""
    tmp_path = f"{os.fspath(path)}.{os.getpid()}.tmp"
    try:
        with open(tmp_path, mode) as handle:
            yield handle
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def download_and_decompress_gz(url: str, cache_dir: str) -> str:
    """Download a .nc.gz file and decompress it. Returns path to .nc file."""
    gz_name = os.path.basename(url)
    nc_name = gz_name.removesuffix(".gz")
    nc_path = os.path.join(cache_dir, nc_name)

    if os.path.isfile(nc_path):
        logger.info("Using cached file: %s", nc_path)
        return nc_path

    gz_path = os.path.join(cache_dir, gz_name)
    logger.info("Downloading %s ...", url)
    resp = requests.get(url, timeout=600, stream=True)
    resp.raise_for_status()
    with open(gz_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)

    logger.info("Decompressing %s ...", gz_name)
    with gzip.open(gz_path, "rb") as fin, atomic_open(nc_path) as fout:
        while chunk := fin.read(65536):
            fout.write(chunk)
    os.unlink(gz_path)
    return nc_path


def filter_by_geojson(
    df: pd.DataFrame,
    region: Union[str, gpd.GeoDataFrame],
) -> pd.DataFrame:
    """Keep only DataFrame points inside a polygon.

    Args:
        df: DataFrame with ``latitude`` and ``longitude`` columns.
        region: GeoJSON file path or a GeoDataFrame with the polygon(s).
    """
    if isinstance(region, str):
        region = gpd.read_file(region)
    if region.crs is not None and region.crs != "EPSG:4326":
        region = region.to_crs("EPSG:4326")

    xmin, ymin, xmax, ymax = region.total_bounds
    df = df[
        (df["latitude"] >= ymin)
        & (df["latitude"] <= ymax)
        & (df["longitude"] >= xmin)
        & (df["longitude"] <= xmax)
    ].copy()
    if df.empty:
        return df

    unique_pts = df[["latitude", "longitude"]].drop_duplicates()
    pts = gpd.GeoDataFrame(
        unique_pts,
        geometry=gpd.points_from_xy(unique_pts["longitude"], unique_pts["latitude"]),
        crs="EPSG:4326",
    )
    inside = gpd.sjoin(pts, region[["geometry"]], how="inner", predicate="within")
    mask = inside[["latitude", "longitude"]]
    return df.merge(mask, on=["latitude", "longitude"]).reset_index(drop=True)


def get_or_create_cache_dir(prefix: str, current: Optional[str]) -> str:
    """Return an existing cache dir or create a new temp one."""
    import tempfile

    if current is not None and os.path.isdir(current):
        return current
    return tempfile.mkdtemp(prefix=prefix)
