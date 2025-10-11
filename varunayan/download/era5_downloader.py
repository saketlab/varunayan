import datetime as dt
import logging
import os
import tempfile
from typing import Dict, List

import cdsapi  # pyright: ignore

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
        # Remove the filter if it exists
        logger.filters = [
            f for f in logger.filters if not isinstance(f, BlockInfoFilter)
        ]
        sup_log = False
    else:
        logger.addFilter(BlockInfoFilter())
        sup_log = True


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

    # Prepare date ranges
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

    # Save to temporary directory
    temp_dir = tempfile.gettempdir()
    output_file = os.path.join(temp_dir, f"{request_id}.zip")

    if frequency in ["monthly", "yearly"]:
        request = {
            "product_type": ["monthly_averaged_reanalysis"],
            "year": years,
            "month": months,
            "time": ["00:00"],
            "variable": variables,
            "area": [north, west, south, east],
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
            "area": [north, west, south, east],
            "grid": [resolution, resolution],
        }

    client = cdsapi.Client()
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

    # Prepare date ranges
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

    # Save to temporary directory
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
            "area": [north, west, south, east],
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
            "area": [north, west, south, east],
            "grid": [resolution, resolution],
            "format": "netcdf",
        }

    client = cdsapi.Client()
    client.retrieve(dataset, request, output_file)

    return output_file
