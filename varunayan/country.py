"""Country-level ERA5 temperature aggregation."""

import logging
import os
import re
from typing import List, Optional, Union

import geopandas as gpd
import numpy as np
import pandas as pd

from ._geo_utils import filter_by_geojson
from .convenience import _convert_era5_units
from .core import era5ify_bbox

logger = logging.getLogger(__name__)

_NE_URL = (
    "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
)

_VAR_SHORTHANDS = {
    "mean": "2m_temperature",
    "max": "maximum_2m_temperature_since_previous_post_processing",
    "min": "minimum_2m_temperature_since_previous_post_processing",
}

_COL_RENAME = {
    "t2m": "temperature_mean",
    "2m_temperature": "temperature_mean",
    "mx2t": "temperature_max",
    "maximum_2m_temperature_since_previous_post_processing": "temperature_max",
    "mn2t": "temperature_min",
    "minimum_2m_temperature_since_previous_post_processing": "temperature_min",
}

_ALIASES = {
    "USA": "United States of America",
    "US": "United States of America",
    "United States": "United States of America",
    "UK": "United Kingdom",
    "Russia": "Russian Federation",
    "Czechia": "Czech Republic",
    "South Korea": "Republic of Korea",
    "North Korea": "Dem. Rep. Korea",
    "Turkiye": "Turkey",
    "Türkiye": "Turkey",
    "Ivory Coast": "Côte d'Ivoire",
    "Eswatini": "eSwatini",
    "Burma": "Myanmar",
    "Timor-Leste": "East Timor",
    "Congo": "Republic of the Congo",
    "DRC": "Democratic Republic of the Congo",
    "DR Congo": "Democratic Republic of the Congo",
    "Tanzania": "United Republic of Tanzania",
    "Bosnia": "Bosnia and Herzegovina",
    "UAE": "United Arab Emirates",
}

_WORLD_CACHE: Optional[gpd.GeoDataFrame] = None


def _get_world() -> gpd.GeoDataFrame:
    global _WORLD_CACHE
    if _WORLD_CACHE is None:
        logger.info("Downloading Natural Earth country boundaries...")
        _WORLD_CACHE = gpd.read_file(_NE_URL)
    return _WORLD_CACHE


def _resolve_country(country: Union[str, gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    """Resolve a country name, ISO code, GeoJSON path, or GeoDataFrame to a polygon."""
    if isinstance(country, gpd.GeoDataFrame):
        return country

    if isinstance(country, str) and os.path.isfile(country):
        return gpd.read_file(country)

    if not isinstance(country, str):
        raise TypeError(
            "country must be a name (str), ISO code, GeoJSON file path, or GeoDataFrame"
        )

    name = _ALIASES.get(country, country)
    world = _get_world()

    name_lower = name.lower()
    match = world[
        (world["NAME"].str.lower() == name_lower)
        | (world["NAME_LONG"].str.lower() == name_lower)
        | (world["ADMIN"].str.lower() == name_lower)
        | (world["ISO_A3"].str.upper() == name.upper())
        | (world["ISO_A2"].str.upper() == name.upper())
    ]

    if match.empty:
        match = world[world["NAME"].str.contains(name, case=False, na=False)]

    if match.empty:
        available = sorted(world["NAME"].dropna().tolist())
        raise ValueError(
            f"Country '{country}' not found in Natural Earth data. "
            f"Try an ISO code or one of: {available[:30]}"
        )

    return match.iloc[[0]]


def get_era5_country_temperature(
    country: Union[str, gpd.GeoDataFrame],
    start_date: str,
    end_date: str,
    variables: Union[str, List[str]] = "mean",
    request_id: Optional[str] = None,
    resolution: float = 0.25,
) -> pd.DataFrame:
    """Download and aggregate ERA5 temperature for a country.

    Resolves the country boundary via Natural Earth, downloads monthly ERA5 data,
    filters grid points to the country polygon, and returns cosine-latitude
    area-weighted national averages by year and month.

    Args:
        country: Country name, ISO-3166 code, GeoJSON file path, or GeoDataFrame.
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        variables: Temperature shorthand(s): "mean", "max", "min", or ERA5 variable names.
        request_id: Cache identifier. Auto-generated from country name if omitted.
        resolution: Spatial resolution in degrees.

    Returns:
        DataFrame with columns year, month, and one per variable
        (temperature_mean, temperature_max, temperature_min).
    """
    if isinstance(variables, str):
        variables = [variables]

    era5_vars = list(dict.fromkeys(_VAR_SHORTHANDS.get(v, v) for v in variables))

    polygon = _resolve_country(country)

    if request_id is None:
        label = country if isinstance(country, str) else "custom"
        request_id = re.sub(r"[^a-zA-Z0-9]", "_", label.lower())

    bbox = polygon.total_bounds
    north, south = float(bbox[3]), float(bbox[1])
    east, west = float(bbox[2]), float(bbox[0])

    raw = era5ify_bbox(
        request_id=request_id,
        variables=era5_vars,
        start_date=start_date,
        end_date=end_date,
        north=north,
        south=south,
        east=east,
        west=west,
        frequency="monthly",
        resolution=resolution,
        save_raw=False,
    )

    raw = _convert_era5_units(raw)
    raw = filter_by_geojson(raw, polygon[["geometry"]])

    dt = pd.to_datetime(raw["datetime"])
    raw["year"] = dt.dt.year
    raw["month"] = dt.dt.month
    raw["_weight"] = np.cos(np.radians(raw["latitude"]))

    rename = {old: new for old, new in _COL_RENAME.items() if old in raw.columns}
    raw = raw.rename(columns=rename)
    value_cols = list(rename.values())

    def _weighted_agg(g: pd.DataFrame) -> pd.Series:
        w = g["_weight"].values
        return pd.Series(
            {col: np.average(g[col].values, weights=w) for col in value_cols}
        )

    result = raw.groupby(["year", "month"]).apply(_weighted_agg).reset_index()
    return result.sort_values(["year", "month"]).reset_index(drop=True)
