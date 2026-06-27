"""CRU TS v4.07 monthly climate grids (0.5 deg, 1901-2022).

Harris et al. (2020) https://doi.org/10.1038/s41597-020-0453-3
"""

import logging
import os
import tempfile
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from ._geo_utils import (
    download_and_decompress_gz,
    filter_by_geojson,
    get_or_create_cache_dir,
)

logger = logging.getLogger(__name__)

_VERSION = "4.07"
_SUBDIR = "cruts.2304141047.v4.07"
_BASE_URL = f"https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_{_VERSION}/{_SUBDIR}"
_YEAR_START = 1901
_YEAR_END = 2022

_DECADES: List[Tuple[int, int]] = [
    (1901, 1910),
    (1911, 1920),
    (1921, 1930),
    (1931, 1940),
    (1941, 1950),
    (1951, 1960),
    (1961, 1970),
    (1971, 1980),
    (1981, 1990),
    (1991, 2000),
    (2001, 2010),
    (2011, 2020),
    (2021, 2022),
]

_VALID_VARIABLES = [
    "tmp",
    "tmx",
    "tmn",
    "dtr",
    "pre",
    "wet",
    "frs",
    "vap",
    "cld",
    "pet",
]

_CACHE_DIR: Optional[str] = None


def _get_cache_dir() -> str:
    global _CACHE_DIR
    _CACHE_DIR = get_or_create_cache_dir("cru_ts_", _CACHE_DIR)
    return _CACHE_DIR


def _build_url(variable: str, decade_start: int, decade_end: int) -> str:
    """Build the download URL for a CRU TS decade file."""
    filename = f"cru_ts{_VERSION}.{decade_start}.{decade_end}.{variable}.dat.nc.gz"
    return f"{_BASE_URL}/{variable}/{filename}"


def _needed_decades(start_year: int, end_year: int) -> List[Tuple[int, int]]:
    """Return the subset of decade files that overlap the requested range."""
    return [(ds, de) for ds, de in _DECADES if de >= start_year and ds <= end_year]


def _parse_time(time_var: np.ndarray, time_units: str) -> List[datetime]:
    """Parse CRU TS time coordinate to a list of datetime objects."""
    units_lower = time_units.strip().lower()
    if "days since" in units_lower:
        base_str = time_units.strip().split("days since")[-1].strip()[:10]
        base = datetime.strptime(base_str, "%Y-%m-%d")
        return [base + timedelta(days=float(d)) for d in time_var]
    if "months since" in units_lower:
        import re

        m = re.search(r"(\d{4})-(\d{2})", time_units)
        if m is None:
            raise ValueError(f"Cannot parse base date from: {time_units}")
        base_year, base_month = int(m.group(1)), int(m.group(2))
        total = base_year * 12 + (base_month - 1) + np.round(time_var).astype(int)
        return [datetime(int(t // 12), int(t % 12 + 1), 1) for t in total]
    raise ValueError(f"Unrecognised time units in CRU TS file: {time_units}")


def _read_nc(nc_path: str, variable: str) -> pd.DataFrame:
    """Read a CRU TS NetCDF file into a DataFrame."""
    import netCDF4

    ds = netCDF4.Dataset(nc_path, "r")
    try:
        lat = ds.variables["lat"][:]
        lon = ds.variables["lon"][:]

        if variable not in ds.variables:
            available = list(ds.variables.keys())
            raise KeyError(f"Variable '{variable}' not found. Available: {available}")

        vals = ds.variables[variable][:]
        fill_val = getattr(ds.variables[variable], "_FillValue", None)

        time_var = ds.variables["time"][:]
        time_units = ds.variables["time"].units
        dates = _parse_time(time_var, time_units)

        n_lon, n_lat, n_time = len(lon), len(lat), len(dates)
        lon_idx: np.ndarray
        lat_idx: np.ndarray
        time_idx: np.ndarray
        lon_idx, lat_idx, time_idx = np.meshgrid(
            np.arange(n_lon), np.arange(n_lat), np.arange(n_time), indexing="ij"
        )
        flat_vals = vals[lon_idx.ravel(), lat_idx.ravel(), time_idx.ravel()]
        mask = ~np.isnan(flat_vals)
        if fill_val is not None:
            mask &= np.abs(flat_vals - fill_val) > 1e-6

        years = np.array([d.year for d in dates])
        months = np.array([d.month for d in dates])

        df = pd.DataFrame(
            {
                "year": years[time_idx.ravel()][mask],
                "month": months[time_idx.ravel()][mask],
                "latitude": lat[lat_idx.ravel()][mask],
                "longitude": lon[lon_idx.ravel()][mask],
                "value": flat_vals[mask],
                "variable": variable,
            }
        )
        return df
    finally:
        ds.close()


def _validate_inputs(variable: str, start_year: int, end_year: int) -> None:
    """Validate CRU TS query parameters."""
    if variable not in _VALID_VARIABLES:
        raise ValueError(
            f"'{variable}' is not a valid CRU TS variable. "
            f"Available: {_VALID_VARIABLES}. See list_cru_ts_variables()."
        )
    if start_year < _YEAR_START or end_year > _YEAR_END:
        raise ValueError(
            f"CRU TS v{_VERSION} covers {_YEAR_START}-{_YEAR_END}. "
            f"Requested: {start_year}-{end_year}."
        )
    if start_year > end_year:
        raise ValueError("start_year must be <= end_year")


def _fetch_data(
    variable: str,
    start_year: int,
    end_year: int,
    use_cache: bool,
) -> pd.DataFrame:
    """Download all needed decade files and combine into one DataFrame."""
    decades = _needed_decades(start_year, end_year)
    cache_dir = _get_cache_dir() if use_cache else tempfile.mkdtemp(prefix="cru_ts_")

    frames: List[pd.DataFrame] = []
    for ds, de in decades:
        url = _build_url(variable, ds, de)
        nc_path = download_and_decompress_gz(url, cache_dir)
        logger.info("Reading NetCDF for %s %d-%d...", variable, ds, de)
        df = _read_nc(nc_path, variable)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined = combined[
        (combined["year"] >= start_year) & (combined["year"] <= end_year)
    ]
    return combined.reset_index(drop=True)


def list_cru_ts_variables() -> pd.DataFrame:
    """Return a DataFrame of all CRU TS variables."""
    return pd.DataFrame(
        {
            "variable": _VALID_VARIABLES,
            "name": [
                "mean_temperature",
                "max_temperature",
                "min_temperature",
                "diurnal_temperature_range",
                "precipitation",
                "wet_day_frequency",
                "frost_day_frequency",
                "vapour_pressure",
                "cloud_cover",
                "potential_evapotranspiration",
            ],
            "description": [
                "Monthly mean daily mean temperature",
                "Monthly mean daily maximum temperature",
                "Monthly mean daily minimum temperature",
                "Monthly mean diurnal temperature range (tmx - tmn)",
                "Monthly total precipitation",
                "Monthly count of wet days (precipitation >= 0.1 mm)",
                "Monthly count of frost days (minimum temperature < 0°C)",
                "Monthly mean vapour pressure",
                "Monthly mean cloud cover (oktas converted to %)",
                "Monthly total potential evapotranspiration (Penman-Monteith)",
            ],
            "unit": [
                "°C",
                "°C",
                "°C",
                "°C",
                "mm/month",
                "days/month",
                "days/month",
                "hPa",
                "%",
                "mm/month",
            ],
            "era5_equivalent": [
                "2m_temperature",
                "maximum_2m_temperature_since_previous_post_processing",
                "minimum_2m_temperature_since_previous_post_processing",
                None,
                "total_precipitation",
                None,
                None,
                "2m_dewpoint_temperature",
                "total_cloud_cover",
                None,
            ],
            "hadex3_equivalent": [
                None,
                "TXx/TXn",
                "TNx/TNn",
                "DTR",
                "PRCPTOT",
                "CWD",
                "FD",
                None,
                None,
                None,
            ],
        }
    )


def cru_ts_bbox(
    variable: str,
    start_year: int,
    end_year: int,
    north: float,
    south: float,
    east: float,
    west: float,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Download CRU TS data filtered to a bounding box."""
    _validate_inputs(variable, start_year, end_year)
    logger.info(
        "CRU TS download: variable=%s, years=%d-%d, bbox=N%s/S%s/E%s/W%s",
        variable,
        start_year,
        end_year,
        north,
        south,
        east,
        west,
    )

    df = _fetch_data(variable, start_year, end_year, use_cache)
    df = df[
        (df["latitude"] >= south)
        & (df["latitude"] <= north)
        & (df["longitude"] >= west)
        & (df["longitude"] <= east)
    ]
    logger.info("Filtered to %d data points.", len(df))
    return df.reset_index(drop=True)


def cru_ts_geojson(
    variable: str,
    start_year: int,
    end_year: int,
    geojson_file: str,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Download CRU TS data filtered to a GeoJSON polygon."""
    _validate_inputs(variable, start_year, end_year)
    if not os.path.isfile(geojson_file):
        raise FileNotFoundError(f"GeoJSON file not found: {geojson_file}")

    logger.info(
        "CRU TS download: variable=%s, years=%d-%d, geojson=%s",
        variable,
        start_year,
        end_year,
        os.path.basename(geojson_file),
    )

    df = _fetch_data(variable, start_year, end_year, use_cache)
    df = filter_by_geojson(df, geojson_file)
    logger.info("Filtered to %d data points.", len(df))
    return df.reset_index(drop=True)
