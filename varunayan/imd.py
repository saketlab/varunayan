"""IMD gridded climate data (rainfall 0.25/1.0 deg, temperature 1.0 deg)."""

from __future__ import annotations

import calendar
import logging
import os
import tempfile
import time
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)


IMD_GRID_SPECS: Dict[str, dict] = {
    "rainfall_0.25": {
        "nlat": 129,
        "nlon": 135,
        "lat_start": 6.5,
        "lat_end": 38.5,
        "lon_start": 66.5,
        "lon_end": 100.0,
        "resolution": 0.25,
        "unit": "mm",
        "missing_value": -999,
        "format": "NetCDF",
    },
    "rainfall_1.0": {
        "nlat": 31,
        "nlon": 31,
        "lat_start": 7.5,
        "lat_end": 37.5,
        "lon_start": 67.5,
        "lon_end": 97.5,
        "resolution": 1.0,
        "unit": "mm",
        "missing_value": -999,
        "format": "NetCDF",
    },
    "tmax_1.0": {
        "nlat": 31,
        "nlon": 31,
        "lat_start": 7.5,
        "lat_end": 37.5,
        "lon_start": 67.5,
        "lon_end": 97.5,
        "resolution": 1.0,
        "unit": "Celsius",
        "missing_value": 99.9,
        "format": "Binary",
    },
    "tmin_1.0": {
        "nlat": 31,
        "nlon": 31,
        "lat_start": 7.5,
        "lat_end": 37.5,
        "lon_start": 67.5,
        "lon_end": 97.5,
        "resolution": 1.0,
        "unit": "Celsius",
        "missing_value": 99.9,
        "format": "Binary",
    },
}

_IMD_BASE_URL = "https://www.imdpune.gov.in/cmpg/Griddata/"
_IMD_ENDPOINTS: Dict[str, dict] = {
    "rainfall_0.25": {"page": "RF25.php", "param": "RF25"},
    "rainfall_1.0": {"page": "rain.php", "param": "rain"},
    "tmax_1.0": {"page": "maxtemp.php", "param": "maxtemp"},
    "tmin_1.0": {"page": "mintemp.php", "param": "mintemp"},
}


def get_imd_grid_specs(dataset: str) -> dict:
    """Return grid specifications for *dataset* (a key in ``IMD_GRID_SPECS``)."""
    if dataset not in IMD_GRID_SPECS:
        raise ValueError(
            f"Unknown dataset '{dataset}'. Choose from: {list(IMD_GRID_SPECS)}"
        )
    return IMD_GRID_SPECS[dataset]


def list_imd_datasets() -> pd.DataFrame:
    """Return a DataFrame of all IMD gridded datasets."""
    rows = []
    for name, s in IMD_GRID_SPECS.items():
        rows.append(
            {
                "dataset": name,
                "nlat": s["nlat"],
                "nlon": s["nlon"],
                "resolution": s["resolution"],
                "unit": s["unit"],
                "format": s["format"],
                "lat_range": f"{s['lat_start']}-{s['lat_end']}",
                "lon_range": f"{s['lon_start']}-{s['lon_end']}",
            }
        )
    return pd.DataFrame(rows)


def _download_imd_year(
    dataset: str, year: int, output_dir: str, use_cache: bool = True
) -> str:
    """Download a single year of IMD data."""
    ep = _IMD_ENDPOINTS[dataset]
    ext = ".nc" if IMD_GRID_SPECS[dataset]["format"] == "NetCDF" else ".grd"
    out_path = os.path.join(output_dir, f"{dataset}_{year}{ext}")

    if use_cache and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        logger.info("Using cached file: %s", out_path)
        return out_path

    url = _IMD_BASE_URL + ep["page"]
    for attempt in range(3):
        try:
            logger.info(
                "Downloading %s year %d (attempt %d/3)", dataset, year, attempt + 1
            )
            resp = requests.post(url, data={ep["param"]: str(year)}, timeout=(60, 600))
            resp.raise_for_status()
            if "text/html" in resp.headers.get("Content-Type", ""):
                raise ValueError(f"Server returned HTML for {dataset} {year}")
            if len(resp.content) == 0:
                raise ValueError(f"Empty response for {dataset} {year}")
            os.makedirs(output_dir, exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(resp.content)
            logger.info("Saved %s (%d bytes)", out_path, len(resp.content))
            return out_path
        except Exception as exc:
            logger.warning("Attempt %d failed: %s", attempt + 1, exc)
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
            else:
                raise
    raise RuntimeError(f"Download failed for {dataset} {year}")


def download_imd_rainfall(
    start_year: int,
    end_year: int,
    resolution: float = 0.25,
    output_dir: Optional[str] = None,
    use_cache: bool = True,
) -> List[str]:
    """Download IMD gridded rainfall for each year. Returns list of file paths."""
    ds = f"rainfall_{resolution}"
    if ds not in IMD_GRID_SPECS:
        raise ValueError(f"Invalid resolution {resolution}. Use 0.25 or 1.0.")
    out = output_dir or os.path.join(tempfile.gettempdir(), "imd_data")
    return [
        _download_imd_year(ds, y, out, use_cache)
        for y in range(start_year, end_year + 1)
    ]


def download_imd_temperature(
    start_year: int,
    end_year: int,
    var_type: str = "tmax",
    output_dir: Optional[str] = None,
    use_cache: bool = True,
) -> List[str]:
    """Download IMD gridded temperature for each year. Returns list of file paths."""
    if var_type not in ("tmax", "tmin"):
        raise ValueError(f"var_type must be 'tmax' or 'tmin', got '{var_type}'")
    ds = f"{var_type}_1.0"
    out = output_dir or os.path.join(tempfile.gettempdir(), "imd_data")
    return [
        _download_imd_year(ds, y, out, use_cache)
        for y in range(start_year, end_year + 1)
    ]


def read_imd_temperature(file_path: str, var_type: str, year: int) -> pd.DataFrame:
    """Read an IMD binary .grd temperature file (32-bit LE floats, nlon x nlat x ndays)."""
    n_days = 366 if calendar.isleap(year) else 365
    specs = IMD_GRID_SPECS[f"{var_type}_1.0"]

    with open(file_path, "rb") as f:
        raw: np.ndarray = np.frombuffer(f.read(), dtype="<f4")

    n_values = n_days * specs["nlat"] * specs["nlon"]
    data_array = raw[:n_values].reshape(
        (specs["nlon"], specs["nlat"], n_days), order="C"
    )

    lats = np.arange(
        specs["lat_start"],
        specs["lat_end"] + specs["resolution"] / 2,
        specs["resolution"],
    )[: specs["nlat"]]
    lons = np.arange(
        specs["lon_start"],
        specs["lon_end"] + specs["resolution"] / 2,
        specs["resolution"],
    )[: specs["nlon"]]
    dates = pd.date_range(f"{year}-01-01", periods=n_days)

    lon_idx: np.ndarray
    lat_idx: np.ndarray
    day_idx: np.ndarray
    lon_idx, lat_idx, day_idx = np.meshgrid(
        np.arange(len(lons)),
        np.arange(len(lats)),
        np.arange(n_days),
        indexing="ij",
    )
    df = pd.DataFrame(
        {
            "date": dates[day_idx.ravel()],
            "latitude": lats[lat_idx.ravel()],
            "longitude": lons[lon_idx.ravel()],
            "temperature": data_array.ravel(),
        }
    )
    return df[df["temperature"] < 99].reset_index(drop=True)


def read_imd_rainfall(file_path: str, resolution: float, year: int) -> pd.DataFrame:
    """Read an IMD NetCDF rainfall file."""
    import xarray as xr

    ds = xr.open_dataset(file_path)
    df = ds.to_dataframe().reset_index()
    rename_map = {"lon": "longitude", "lat": "latitude", "time": "date"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    rf_col = None
    for candidate in ("rf", "rainfall", "rain", "precip", "RAINFALL"):
        if candidate in df.columns:
            rf_col = candidate
            break
    if rf_col is None:
        data_vars = [
            c for c in df.columns if c not in ("date", "latitude", "longitude")
        ]
        rf_col = data_vars[0] if data_vars else None
    if rf_col is None:
        raise ValueError(f"No rainfall variable found in {file_path}")
    if rf_col != "rainfall":
        df = df.rename(columns={rf_col: "rainfall"})
    return df[df["rainfall"] > -900][
        ["date", "latitude", "longitude", "rainfall"]
    ].reset_index(drop=True)


def process_imd_files(
    file_paths: List[str],
    var_type: str,
    resolution: Optional[float] = None,
    years: Optional[List[int]] = None,
) -> pd.DataFrame:
    """Read and concatenate multiple IMD files."""
    frames: List[pd.DataFrame] = []
    for i, fp in enumerate(file_paths):
        yr = (
            years[i]
            if years
            else int(os.path.splitext(os.path.basename(fp))[0].split("_")[-1])
        )
        if var_type == "rainfall":
            if resolution is None:
                raise ValueError("resolution is required for rainfall files")
            frames.append(read_imd_rainfall(fp, resolution, yr))
        else:
            frames.append(read_imd_temperature(fp, var_type, yr))
    return pd.concat(frames, ignore_index=True)


def filter_imd_by_bbox(
    data: pd.DataFrame,
    north: float,
    south: float,
    east: float,
    west: float,
) -> pd.DataFrame:
    """Filter IMD data to a lat/lon bounding box."""
    return data[
        (data["latitude"] >= south)
        & (data["latitude"] <= north)
        & (data["longitude"] >= west)
        & (data["longitude"] <= east)
    ].reset_index(drop=True)


def filter_imd_by_geojson(data: pd.DataFrame, geojson_file: str) -> pd.DataFrame:
    """Filter IMD data to points within a GeoJSON polygon."""
    from ._geo_utils import filter_by_geojson

    return filter_by_geojson(data, geojson_file)


def aggregate_imd_by_frequency(
    data: pd.DataFrame, frequency: str = "daily"
) -> pd.DataFrame:
    """Aggregate IMD data: SUM for rainfall, MEAN for temperature."""
    if frequency == "daily":
        return data

    value_col = "rainfall" if "rainfall" in data.columns else "temperature"
    agg_func = "sum" if value_col == "rainfall" else "mean"
    df = data.copy()
    df["date"] = pd.to_datetime(df["date"])

    if frequency == "weekly":
        df["period"] = df["date"].dt.isocalendar().week.astype(int)
        df["year"] = df["date"].dt.year
        group_cols = ["year", "period", "latitude", "longitude"]
    elif frequency == "monthly":
        df["period"] = df["date"].dt.month
        df["year"] = df["date"].dt.year
        group_cols = ["year", "period", "latitude", "longitude"]
    elif frequency == "yearly":
        df["year"] = df["date"].dt.year
        group_cols = ["year", "latitude", "longitude"]
    else:
        raise ValueError(f"Unknown frequency '{frequency}'")

    return df.groupby(group_cols, as_index=False).agg({value_col: agg_func})


def _pipeline(
    request_id: str,
    start_year: int,
    end_year: int,
    var_type: str,
    frequency: str,
    use_cache: bool,
    resolution: Optional[float],
    filter_fn: Callable[[pd.DataFrame], pd.DataFrame],
) -> pd.DataFrame:
    """Download, read, filter, aggregate."""
    years = list(range(start_year, end_year + 1))
    if var_type == "rainfall":
        res = resolution if resolution is not None else 0.25
        logger.info(
            "Pipeline '%s': rainfall %.2f deg, %d-%d",
            request_id,
            res,
            start_year,
            end_year,
        )
        files = download_imd_rainfall(start_year, end_year, res, use_cache=use_cache)
        data = process_imd_files(files, "rainfall", resolution=res, years=years)
    else:
        logger.info(
            "Pipeline '%s': %s, %d-%d", request_id, var_type, start_year, end_year
        )
        files = download_imd_temperature(
            start_year, end_year, var_type, use_cache=use_cache
        )
        data = process_imd_files(files, var_type, years=years)
    return aggregate_imd_by_frequency(filter_fn(data), frequency)


def imd_rainfall_bbox(
    request_id: str,
    start_year: int,
    end_year: int,
    north: float,
    south: float,
    east: float,
    west: float,
    resolution: float = 0.25,
    frequency: str = "daily",
    use_cache: bool = True,
) -> pd.DataFrame:
    """Download, bbox-filter, aggregate IMD rainfall."""
    return _pipeline(
        request_id,
        start_year,
        end_year,
        "rainfall",
        frequency,
        use_cache,
        resolution,
        lambda d: filter_imd_by_bbox(d, north, south, east, west),
    )


def imd_rainfall_geojson(
    request_id: str,
    start_year: int,
    end_year: int,
    geojson_file: str,
    resolution: float = 0.25,
    frequency: str = "daily",
    use_cache: bool = True,
) -> pd.DataFrame:
    """Download, geojson-filter, aggregate IMD rainfall."""
    return _pipeline(
        request_id,
        start_year,
        end_year,
        "rainfall",
        frequency,
        use_cache,
        resolution,
        lambda d: filter_imd_by_geojson(d, geojson_file),
    )


def imd_temperature_bbox(
    request_id: str,
    start_year: int,
    end_year: int,
    north: float,
    south: float,
    east: float,
    west: float,
    var_type: str = "tmax",
    frequency: str = "daily",
    use_cache: bool = True,
) -> pd.DataFrame:
    """Download, bbox-filter, aggregate IMD temperature."""
    return _pipeline(
        request_id,
        start_year,
        end_year,
        var_type,
        frequency,
        use_cache,
        None,
        lambda d: filter_imd_by_bbox(d, north, south, east, west),
    )


def imd_temperature_geojson(
    request_id: str,
    start_year: int,
    end_year: int,
    geojson_file: str,
    var_type: str = "tmax",
    frequency: str = "daily",
    use_cache: bool = True,
) -> pd.DataFrame:
    """Download, geojson-filter, aggregate IMD temperature."""
    return _pipeline(
        request_id,
        start_year,
        end_year,
        var_type,
        frequency,
        use_cache,
        None,
        lambda d: filter_imd_by_geojson(d, geojson_file),
    )
