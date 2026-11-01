import datetime as dt
import logging
import math
import os
import tempfile
from typing import TYPE_CHECKING, Dict, List

import cdsapi  # pyright: ignore

if TYPE_CHECKING:
    import pandas as pd

sup_log: bool = False


class BlockInfoFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno != logging.INFO


def set_v_downloader(verbosity: int) -> None:
    global sup_log
    logger = logging.getLogger("datapi.legacy_api_client")

    if verbosity == 0:
        logger.addFilter(BlockInfoFilter())
        sup_log = True
    elif verbosity == 1 or verbosity == 2:
        logger.filters = [
            f for f in logger.filters if not isinstance(f, BlockInfoFilter)
        ]
        sup_log = False
    else:
        logger.addFilter(BlockInfoFilter())
        sup_log = True


def _grid_area(
    north: float, west: float, south: float, east: float, resolution: float
) -> List[float]:
    """Snap the area outward to multiples of the resolution.

    CDS aligns the output grid to the corner of the area, so an area such as
    north=37.1 gives cells at 37.1, 36.85, ... Snapping keeps the cells on
    the standard ERA5 grid (the R package does the same).
    """
    k = 1 / resolution
    return [
        min(math.ceil(north * k - 1e-9) / k, 90.0),
        max(math.floor(west * k + 1e-9) / k, -180.0),
        max(math.floor(south * k + 1e-9) / k, -90.0),
        min(math.ceil(east * k - 1e-9) / k, 180.0),
    ]


def download_era5_single_lvl(
    request_id: str,
    variables: List[str],
    start_date: dt.datetime,
    end_date: dt.datetime,
    north: float,
    west: float,
    south: float,
    east: float,
    resolution: float = 0.25,
    frequency: str = "hourly",
) -> str:
    """Download ERA5 single levels data."""
    frequency = frequency.lower()

    dataset = (
        "reanalysis-era5-single-levels-monthly-means"
        if frequency in ["monthly", "yearly"]
        else "reanalysis-era5-single-levels"
    )

    dates: Dict[str, Dict[str, List[str]]] = {}
    current_date = start_date
    while current_date <= end_date:
        year = str(current_date.year)
        if year not in dates:
            dates[year] = {}
        month = str(current_date.month).zfill(2)
        if month not in dates[year]:
            dates[year][month] = []
        dates[year][month].append(str(current_date.day).zfill(2))
        current_date += dt.timedelta(days=1)

    years: List[str] = list(dates.keys())
    months: List[str] = []
    days: List[str] = []
    for year in dates:
        for month in dates[year]:
            if month not in months:
                months.append(month)
            for day in dates[year][month]:
                if day not in days:
                    days.append(day)

    temp_dir = tempfile.gettempdir()
    output_file = os.path.join(temp_dir, f"{request_id}.zip")

    if frequency in ["monthly", "yearly"]:
        request = {
            "product_type": ["monthly_averaged_reanalysis"],
            "year": years,
            "month": months,
            "time": ["00:00"],
            "variable": variables,
            "area": _grid_area(north, west, south, east, resolution),
            "data_format": "netcdf",
            "download_format": "zip",
            "grid": [resolution, resolution],
        }
    else:
        hours = [f"{h:02d}:00" for h in range(24)]
        request = {
            "product_type": ["reanalysis"],
            "year": years,
            "month": months,
            "day": days,
            "time": hours,
            "data_format": "netcdf",
            "download_format": "zip",
            "variable": variables,
            "area": _grid_area(north, west, south, east, resolution),
            "grid": [resolution, resolution],
        }

    client = cdsapi.Client(quiet=sup_log, progress=not sup_log)
    client.retrieve(dataset, request, output_file)

    return output_file


def download_era5_pressure_lvl(
    request_id: str,
    variables: List[str],
    start_date: dt.datetime,
    end_date: dt.datetime,
    north: float,
    west: float,
    south: float,
    east: float,
    pressure_levels: List[str],
    resolution: float = 0.25,
    frequency: str = "hourly",
) -> str:
    """Download ERA5 pressure levels data."""
    frequency = frequency.lower()

    dataset = (
        "reanalysis-era5-pressure-levels-monthly-means"
        if frequency in ["monthly", "yearly"]
        else "reanalysis-era5-pressure-levels"
    )

    dates: Dict[str, Dict[str, List[str]]] = {}
    current_date = start_date
    while current_date <= end_date:
        year = str(current_date.year)
        if year not in dates:
            dates[year] = {}
        month = str(current_date.month).zfill(2)
        if month not in dates[year]:
            dates[year][month] = []
        dates[year][month].append(str(current_date.day).zfill(2))
        current_date += dt.timedelta(days=1)

    years: List[str] = list(dates.keys())
    months: List[str] = []
    days: List[str] = []
    for year in dates:
        for month in dates[year]:
            if month not in months:
                months.append(month)
            for day in dates[year][month]:
                if day not in days:
                    days.append(day)

    temp_dir = tempfile.gettempdir()
    output_file = os.path.join(temp_dir, f"{request_id}.nc")

    if frequency in ["monthly", "yearly"]:
        request = {
            "product_type": "monthly_averaged_reanalysis",
            "variable": variables,
            "pressure_level": pressure_levels,
            "year": years,
            "month": months,
            "time": ["00:00"],
            "area": _grid_area(north, west, south, east, resolution),
            "grid": [resolution, resolution],
            "format": "netcdf",
        }
    else:
        hours = [f"{h:02d}:00" for h in range(24)]
        request = {
            "product_type": "reanalysis",
            "variable": variables,
            "pressure_level": pressure_levels,
            "year": years,
            "month": months,
            "day": days,
            "time": hours,
            "area": _grid_area(north, west, south, east, resolution),
            "grid": [resolution, resolution],
            "format": "netcdf",
        }

    client = cdsapi.Client(quiet=sup_log, progress=not sup_log)
    client.retrieve(dataset, request, output_file)

    return output_file


TIMESERIES_DATASET = "reanalysis-era5-single-levels-timeseries"


def download_era5_timeseries(
    variables: List[str],
    start_date: dt.datetime,
    end_date: dt.datetime,
    lat: float,
    lon: float,
) -> "pd.DataFrame":
    """Hourly single-level ERA5 at one point from the CDS time-series endpoint.

    The endpoint returns the series of the nearest grid cell directly. The R
    package uses the same endpoint.

    Args:
        variables: ERA5 variable names, such as ["2m_temperature"].
        start_date: First day.
        end_date: Last day (inclusive).
        lat: Latitude of the point.
        lon: Longitude of the point.

    Returns:
        Wide DataFrame with valid_time, latitude and longitude (of the grid
        cell) and one column per variable (short names, ERA5 units).
    """
    import zipfile

    import pandas as pd

    request = {
        "variable": list(variables),
        "location": {"latitude": lat, "longitude": lon},
        "date": [f"{start_date:%Y-%m-%d}/{end_date:%Y-%m-%d}"],
        "data_format": "csv",
    }
    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, "timeseries.zip")
        cdsapi.Client(quiet=sup_log).retrieve(TIMESERIES_DATASET, request, target)
        if zipfile.is_zipfile(target):
            with zipfile.ZipFile(target) as z:
                name = next(n for n in z.namelist() if n.endswith(".csv"))
                with z.open(name) as f:
                    df = pd.read_csv(f)
        else:
            df = pd.read_csv(target)
    df["valid_time"] = pd.to_datetime(df["valid_time"])
    # ERA5 starts at 1940-01-01 07:00 UTC; CDS returns empty values before it
    return df.dropna(
        subset=[
            c for c in df.columns if c not in ("valid_time", "latitude", "longitude")
        ],
        how="all",
    )
