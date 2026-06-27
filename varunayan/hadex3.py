"""HadEX3 ETCCDI climate extremes (1901-2018, 1.25x1.875 deg).

Dunn et al. (2020) https://doi.org/10.1029/2019JD032263
"""

import logging
import os
import re
import tempfile
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from ._geo_utils import (
    download_and_decompress_gz,
    filter_by_geojson,
    get_or_create_cache_dir,
)

logger = logging.getLogger(__name__)

_BASE_URL = "http://www.metoffice.gov.uk/hadobs/hadex3/data"
_YEAR_START = 1901
_YEAR_END = 2018

_ANNUAL_INDICES = [
    "TXx",
    "TXn",
    "TNx",
    "TNn",
    "TX90p",
    "TX10p",
    "TN90p",
    "TN10p",
    "TR",
    "SU",
    "FD",
    "ID",
    "CSDI",
    "WSDI",
    "DTR",
    "GSL",
    "ETR",
    "CDD",
    "CWD",
    "PRCPTOT",
    "R10mm",
    "R20mm",
    "Rx1day",
    "Rx5day",
    "R95p",
    "R99p",
    "R95pTOT",
    "R99pTOT",
    "SDII",
]
_MONTHLY_INDICES = [
    "TXx",
    "TXn",
    "TNx",
    "TNn",
    "TX90p",
    "TX10p",
    "TN90p",
    "TN10p",
    "TR",
    "SU",
    "FD",
    "ID",
    "DTR",
    "ETR",
    "PRCPTOT",
    "Rx1day",
    "Rx5day",
    "SDII",
]
_81_10_INDICES = [
    "TX90p",
    "TX10p",
    "TN90p",
    "TN10p",
    "CSDI",
    "WSDI",
    "R95p",
    "R99p",
    "R95pTOT",
    "R99pTOT",
]

_CACHE_DIR: Optional[str] = None


def _get_cache_dir() -> str:
    global _CACHE_DIR
    _CACHE_DIR = get_or_create_cache_dir("hadex3_", _CACHE_DIR)
    return _CACHE_DIR


def _build_url(index: str, frequency: str, baseline: str) -> str:
    if frequency == "monthly":
        return f"{_BASE_URL}/HadEX3_{index}_MON.nc.gz"
    return f"{_BASE_URL}/HadEX3_{index}_1901-2018_ADW_{baseline}_1.25x1.875deg.nc.gz"


def _parse_time(
    time_var: np.ndarray, time_units: str, frequency: str
) -> tuple:
    """Parse time coordinate to (years,) or (years, months)."""
    u = time_units.strip().lower()
    if frequency == "annual":
        if u == "years":
            return (np.round(time_var).astype(int),)
        if "years since" in u:
            m = re.search(r"(\d{4})", time_units)
            base_year = int(m.group(1)) if m else 0
            return ((base_year + np.round(time_var)).astype(int),)
        if "days since" in u:
            base_str = time_units.split("days since")[-1].strip()[:10]
            base_dt = datetime.strptime(base_str, "%Y-%m-%d")
            return (
                np.array([(base_dt + timedelta(days=float(d))).year for d in time_var]),
            )
        return (np.round(time_var).astype(int),)

    if "months since" in u:
        m = re.search(r"(\d{4})-(\d{2})", time_units)
        if m is None:
            raise ValueError(f"Cannot parse base date from: {time_units}")
        by, bm = int(m.group(1)), int(m.group(2))
        total = by * 12 + (bm - 1) + np.round(time_var).astype(int)
        return total // 12, total % 12 + 1
    if "days since" in u:
        base_str = time_units.split("days since")[-1].strip()[:10]
        base_dt = datetime.strptime(base_str, "%Y-%m-%d")
        dates = [base_dt + timedelta(days=float(d)) for d in time_var]
        return np.array([d.year for d in dates]), np.array([d.month for d in dates])
    raise ValueError(f"Unrecognised time units in monthly HadEX3 file: {time_units}")


def _read_nc(nc_path: str, index: str, frequency: str) -> pd.DataFrame:
    """Read a HadEX3 NetCDF file into a long-format DataFrame."""
    import netCDF4

    ds = netCDF4.Dataset(nc_path, "r")
    try:
        lat = ds.variables["latitude"][:]
        lon = np.where(
            ds.variables["longitude"][:] > 180,
            ds.variables["longitude"][:] - 360,
            ds.variables["longitude"][:],
        )
        var_name = "Ann" if frequency == "annual" else index
        if var_name not in ds.variables:
            raise KeyError(
                f"Variable '{var_name}' not found. Available: {list(ds.variables.keys())}"
            )
        vals = ds.variables[var_name][:]
        fill_val = getattr(ds.variables[var_name], "_FillValue", None)
        parsed = _parse_time(
            ds.variables["time"][:], ds.variables["time"].units, frequency
        )
    finally:
        ds.close()

    years = parsed[0]
    li: np.ndarray
    ai: np.ndarray
    ti: np.ndarray
    li, ai, ti = np.meshgrid(
        np.arange(len(lon)), np.arange(len(lat)), np.arange(len(years)), indexing="ij"
    )
    flat = vals[li.ravel(), ai.ravel(), ti.ravel()]
    mask = ~np.isnan(flat)
    if fill_val is not None:
        mask &= np.abs(flat - fill_val) > 1e-6
    cols = {
        "year": years[ti.ravel()][mask],
        **({"month": parsed[1][ti.ravel()][mask]} if len(parsed) == 2 else {}),
        "latitude": lat[ai.ravel()][mask],
        "longitude": lon[li.ravel()][mask],
        "value": flat[mask],
        "index": index,
    }
    return pd.DataFrame(cols)


def _validate(
    index: str, frequency: str, baseline: str, start_year: int, end_year: int
) -> None:
    valid = _MONTHLY_INDICES if frequency == "monthly" else _ANNUAL_INDICES
    if index not in valid:
        raise ValueError(
            f"'{index}' not available for {frequency} data. Available: {valid}"
        )
    if frequency == "annual" and baseline not in ("61-90", "81-10"):
        raise ValueError(f"baseline must be '61-90' or '81-10', got '{baseline}'")
    if baseline == "81-10" and index not in _81_10_INDICES:
        raise ValueError(f"Baseline '81-10' only available for: {_81_10_INDICES}")
    if start_year < _YEAR_START or end_year > _YEAR_END:
        raise ValueError(
            f"HadEX3 covers {_YEAR_START}-{_YEAR_END}. Requested: {start_year}-{end_year}."
        )
    if start_year > end_year:
        raise ValueError("start_year must be <= end_year")


# fmt: off
_INDEX_META = {
    "desc": [
        "Max of daily max temp (hottest day)", "Min of daily max temp (coldest day)",
        "Max of daily min temp (warmest night)", "Min of daily min temp (coldest night)",
        "% days TX > 90th pctl", "% days TX < 10th pctl",
        "% days TN > 90th pctl", "% days TN < 10th pctl",
        "Tropical nights (TN > 20°C)", "Summer days (TX > 25°C)",
        "Frost days (TN < 0°C)", "Ice days (TX < 0°C)",
        "Cold spell duration index", "Warm spell duration index",
        "Diurnal temperature range", "Growing season length",
        "Intra-annual extreme temp range",
        "Consecutive dry days (P < 1 mm)", "Consecutive wet days (P >= 1 mm)",
        "Total wet-day precipitation", "Heavy precip days (P >= 10 mm)",
        "Very heavy precip days (P >= 20 mm)", "Max 1-day precipitation",
        "Max 5-day precipitation", "Precip > 95th pctl total",
        "Precip > 99th pctl total", "Fraction from R95p days",
        "Fraction from R99p days", "Simple daily intensity index",
    ],
    "cat": (["Temperature"] * 4 + ["Temperature percentile"] * 4
            + ["Temperature threshold"] * 4
            + ["Temperature duration"] * 2 + ["Temperature"] * 3
            + ["Precipitation"] * 12),
    "unit": ((["°C"] * 4) + (["%"] * 4) + (["days"] * 4)
             + ["days", "days", "°C", "days", "°C"]
             + ["days", "days", "mm", "days", "days",
                "mm", "mm", "mm", "mm", "%", "%", "mm/day"]),
    "monthly": [
        True, True, True, True, True, True, True, True,
        True, True, True, True, False, False, True, False, True,
        False, False, True, False, False, True, True, False, False,
        False, False, True,
    ],
}
# fmt: on


def list_hadex3_indices(frequency: str = "all") -> pd.DataFrame:
    """Return a DataFrame of all ETCCDI indices."""
    if frequency not in ("all", "annual", "monthly"):
        raise ValueError(
            f"frequency must be 'all', 'annual', or 'monthly', got '{frequency}'"
        )
    df = pd.DataFrame(
        {
            "index": _ANNUAL_INDICES,
            "category": _INDEX_META["cat"],
            "description": _INDEX_META["desc"],
            "unit": _INDEX_META["unit"],
            "annual": True,
            "monthly": _INDEX_META["monthly"],
        }
    )
    if frequency == "annual":
        df = df[df["annual"]].reset_index(drop=True)
    elif frequency == "monthly":
        df = df[df["monthly"]].reset_index(drop=True)
    return df


def hadex3_bbox(
    index: str,
    start_year: int,
    end_year: int,
    north: float,
    south: float,
    east: float,
    west: float,
    frequency: str = "annual",
    baseline: str = "61-90",
    use_cache: bool = True,
) -> pd.DataFrame:
    """Download HadEX3 data filtered to a bounding box."""
    _validate(index, frequency, baseline, start_year, end_year)
    cdir = _get_cache_dir() if use_cache else tempfile.mkdtemp(prefix="hadex3_")
    nc_path = download_and_decompress_gz(_build_url(index, frequency, baseline), cdir)
    logger.info("Reading NetCDF for %s (%s)...", index, frequency)
    df = _read_nc(nc_path, index, frequency)
    df = df[(df["year"] >= start_year) & (df["year"] <= end_year)]
    df = df[
        (df["latitude"] >= south)
        & (df["latitude"] <= north)
        & (df["longitude"] >= west)
        & (df["longitude"] <= east)
    ]
    logger.info("Filtered to %d data points.", len(df))
    return df.reset_index(drop=True)


def hadex3_geojson(
    index: str,
    start_year: int,
    end_year: int,
    geojson_file: str,
    frequency: str = "annual",
    baseline: str = "61-90",
    use_cache: bool = True,
) -> pd.DataFrame:
    """Download HadEX3 data filtered to a GeoJSON polygon."""
    _validate(index, frequency, baseline, start_year, end_year)
    if not os.path.isfile(geojson_file):
        raise FileNotFoundError(f"GeoJSON file not found: {geojson_file}")
    cdir = _get_cache_dir() if use_cache else tempfile.mkdtemp(prefix="hadex3_")
    nc_path = download_and_decompress_gz(_build_url(index, frequency, baseline), cdir)
    logger.info("Reading NetCDF for %s (%s)...", index, frequency)
    df = _read_nc(nc_path, index, frequency)
    df = df[(df["year"] >= start_year) & (df["year"] <= end_year)]
    df = filter_by_geojson(df, geojson_file)
    logger.info("Filtered to %d data points.", len(df))
    return df.reset_index(drop=True)
