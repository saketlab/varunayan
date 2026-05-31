"""
Convenience wrapper functions for common climate data workflows.

These functions combine data download with derived metric calculations,
reducing user code from ~30 lines to a single function call.
"""

from typing import List, Optional

import numpy as np
import pandas as pd

from .core import era5ify_bbox, era5ify_geojson, era5ify_point
from .heat_stress import (
    heat_index,
    heat_index_risk_category,
    humidex,
    mean_radiant_temperature,
    relative_humidity_from_dewpoint,
    utci,
    utci_category,
    wbgt_risk_category,
    wbgt_simple,
    wet_bulb_temperature,
)

# Base variables required to compute the full set of heat stress indices.
_HEAT_INDEX_VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
]


def _convert_era5_units(df: pd.DataFrame) -> pd.DataFrame:
    """Convert ERA5 units to user-friendly units."""
    df = df.copy()

    temp_cols = [
        "t2m",
        "d2m",
        "2m_temperature",
        "2m_dewpoint_temperature",
        "maximum_2m_temperature_since_previous_post_processing",
        "minimum_2m_temperature_since_previous_post_processing",
    ]
    for col in temp_cols:
        if col in df.columns:
            if df[col].mean() > 100:
                df[col] = df[col] - 273.15

    precip_cols = ["tp", "total_precipitation"]
    for col in precip_cols:
        if col in df.columns:
            if df[col].max() < 1:
                df[col] = df[col] * 1000

    return df


def _calculate_wind_speed(df: pd.DataFrame) -> pd.Series:
    """Calculate wind speed from u and v components."""
    u_col = None
    v_col = None

    for col in df.columns:
        if "u10" in col.lower() or "10m_u" in col.lower():
            u_col = col
        if "v10" in col.lower() or "10m_v" in col.lower():
            v_col = col

    if u_col and v_col:
        return np.sqrt(df[u_col] ** 2 + df[v_col] ** 2)
    return pd.Series([np.nan] * len(df))


def _heat_index_variables(solar_load: bool) -> List[str]:
    """Variable list for heat index downloads, optionally with solar radiation."""
    variables = list(_HEAT_INDEX_VARIABLES)
    if solar_load:
        variables.append("surface_solar_radiation_downwards")
    return variables


def _apply_heat_index_calculations(
    df: pd.DataFrame, solar_load: bool = False
) -> pd.DataFrame:
    """
    Convert units and derive all heat stress indices on a raw ERA5 DataFrame.

    Returns the DataFrame with temp_c/dewpoint_c, wind_speed, rh, wet_bulb,
    heat_index, wbgt, humidex, utci and their risk categories populated.
    """
    df = _convert_era5_units(df)

    if "t2m" in df.columns:
        df = df.rename(columns={"t2m": "temp_c"})
    if "d2m" in df.columns:
        df = df.rename(columns={"d2m": "dewpoint_c"})

    df["wind_speed"] = _calculate_wind_speed(df)

    if "temp_c" in df.columns and "dewpoint_c" in df.columns:
        df["rh"] = relative_humidity_from_dewpoint(df["temp_c"], df["dewpoint_c"])
        df["wet_bulb"] = wet_bulb_temperature(df["temp_c"], df["rh"])
        df["heat_index"] = heat_index(df["temp_c"], df["rh"])
        df["wbgt"] = wbgt_simple(df["temp_c"], df["dewpoint_c"])
        df["humidex"] = humidex(df["temp_c"], df["dewpoint_c"])

        mrt = None
        if solar_load and "ssrd" in df.columns:
            solar_wm2 = df["ssrd"] / 86400
            mrt = mean_radiant_temperature(df["temp_c"], solar_wm2, df["wind_speed"])
            df["mrt"] = mrt

        df["utci"] = utci(df["temp_c"], df["rh"], df["wind_speed"], mrt)

        df["heat_index_risk"] = heat_index_risk_category(df["heat_index"])
        df["wbgt_risk"] = wbgt_risk_category(df["wbgt"])
        df["utci_stress"] = utci_category(df["utci"])

    return df


def get_era5_daily_temperature(
    request_id: str,
    start_date: str,
    end_date: str,
    north: float,
    south: float,
    east: float,
    west: float,
    resolution: float = 0.25,
    verbosity: int = 0,
) -> pd.DataFrame:
    """
    Download ERA5 daily temperature data with automatic unit conversion.

    Args:
        request_id: Unique identifier for the request
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        north: Northern latitude bound
        south: Southern latitude bound
        east: Eastern longitude bound
        west: Western longitude bound
        resolution: Spatial resolution in degrees (default 0.25)
        verbosity: Logging verbosity level (0-2)

    Returns:
        DataFrame with columns: latitude, longitude, date, temp_c
    """
    variables = ["2m_temperature"]

    df = era5ify_bbox(
        request_id=request_id,
        variables=variables,
        start_date=start_date,
        end_date=end_date,
        north=north,
        south=south,
        east=east,
        west=west,
        frequency="daily",
        resolution=resolution,
        verbosity=verbosity,
        save_raw=False,
    )

    df = _convert_era5_units(df)

    if "t2m" in df.columns:
        df = df.rename(columns={"t2m": "temp_c"})

    return df


def get_era5_daily_humidity(
    request_id: str,
    start_date: str,
    end_date: str,
    north: float,
    south: float,
    east: float,
    west: float,
    resolution: float = 0.25,
    verbosity: int = 0,
) -> pd.DataFrame:
    """
    Download ERA5 daily humidity data with automatic RH calculation.

    Args:
        request_id: Unique identifier for the request
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        north: Northern latitude bound
        south: Southern latitude bound
        east: Eastern longitude bound
        west: Western longitude bound
        resolution: Spatial resolution in degrees (default 0.25)
        verbosity: Logging verbosity level (0-2)

    Returns:
        DataFrame with columns: latitude, longitude, date, temp_c, dewpoint_c, rh
    """
    variables = ["2m_temperature", "2m_dewpoint_temperature"]

    df = era5ify_bbox(
        request_id=request_id,
        variables=variables,
        start_date=start_date,
        end_date=end_date,
        north=north,
        south=south,
        east=east,
        west=west,
        frequency="daily",
        resolution=resolution,
        verbosity=verbosity,
        save_raw=False,
    )

    df = _convert_era5_units(df)

    if "t2m" in df.columns:
        df = df.rename(columns={"t2m": "temp_c"})
    if "d2m" in df.columns:
        df = df.rename(columns={"d2m": "dewpoint_c"})

    if "temp_c" in df.columns and "dewpoint_c" in df.columns:
        df["rh"] = relative_humidity_from_dewpoint(df["temp_c"], df["dewpoint_c"])

    return df


def get_era5_daily_wind(
    request_id: str,
    start_date: str,
    end_date: str,
    north: float,
    south: float,
    east: float,
    west: float,
    resolution: float = 0.25,
    verbosity: int = 0,
) -> pd.DataFrame:
    """
    Download ERA5 daily wind data with automatic wind speed calculation.

    Args:
        request_id: Unique identifier for the request
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        north: Northern latitude bound
        south: Southern latitude bound
        east: Eastern longitude bound
        west: Western longitude bound
        resolution: Spatial resolution in degrees (default 0.25)
        verbosity: Logging verbosity level (0-2)

    Returns:
        DataFrame with columns: latitude, longitude, date, u10, v10, wind_speed
    """
    variables = ["10m_u_component_of_wind", "10m_v_component_of_wind"]

    df = era5ify_bbox(
        request_id=request_id,
        variables=variables,
        start_date=start_date,
        end_date=end_date,
        north=north,
        south=south,
        east=east,
        west=west,
        frequency="daily",
        resolution=resolution,
        verbosity=verbosity,
        save_raw=False,
    )

    df["wind_speed"] = _calculate_wind_speed(df)

    return df


def get_era5_daily_heat_index_data(
    request_id: str,
    start_date: str,
    end_date: str,
    north: float,
    south: float,
    east: float,
    west: float,
    solar_load: bool = False,
    resolution: float = 0.25,
    verbosity: int = 0,
) -> pd.DataFrame:
    """
    Download ERA5 daily data and calculate comprehensive heat stress indices.

    This convenience function downloads temperature, humidity, and wind data,
    then calculates all common heat stress indices in one call.

    Args:
        request_id: Unique identifier for the request
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        north: Northern latitude bound
        south: Southern latitude bound
        east: Eastern longitude bound
        west: Western longitude bound
        solar_load: If True, also download solar radiation for outdoor UTCI
        resolution: Spatial resolution in degrees (default 0.25)
        verbosity: Logging verbosity level (0-2)

    Returns:
        DataFrame with columns:
        - latitude, longitude, date (or year, month, day depending on aggregation)
        - temp_c: Temperature in Celsius
        - dewpoint_c: Dewpoint temperature in Celsius
        - rh: Relative humidity (%)
        - wind_speed: Wind speed in m/s
        - wet_bulb: Wet bulb temperature (°C)
        - heat_index: Heat index (°C)
        - wbgt: Wet Bulb Globe Temperature (°C)
        - humidex: Humidex value
        - utci: Universal Thermal Climate Index (°C)
        - heat_index_risk: NWS risk category
        - wbgt_risk: Occupational risk category
        - utci_stress: Thermal stress category
        - If solar_load=True: ssrd (solar radiation) and mrt (mean radiant temp)
    """
    df = era5ify_bbox(
        request_id=request_id,
        variables=_heat_index_variables(solar_load),
        start_date=start_date,
        end_date=end_date,
        north=north,
        south=south,
        east=east,
        west=west,
        frequency="daily",
        resolution=resolution,
        verbosity=verbosity,
        save_raw=False,
    )

    return _apply_heat_index_calculations(df, solar_load)


def get_era5_monthly_heat_index_data(
    request_id: str,
    start_date: str,
    end_date: str,
    north: float,
    south: float,
    east: float,
    west: float,
    solar_load: bool = False,
    resolution: float = 0.25,
    verbosity: int = 0,
) -> pd.DataFrame:
    """
    Download ERA5 monthly data and calculate comprehensive heat stress indices.

    Same as get_era5_daily_heat_index_data but aggregated to monthly frequency.

    Args:
        request_id: Unique identifier for the request
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        north: Northern latitude bound
        south: Southern latitude bound
        east: Eastern longitude bound
        west: Western longitude bound
        solar_load: If True, also download solar radiation for outdoor UTCI
        resolution: Spatial resolution in degrees (default 0.25)
        verbosity: Logging verbosity level (0-2)

    Returns:
        DataFrame with same columns as get_era5_daily_heat_index_data,
        aggregated to monthly means.
    """
    df = era5ify_bbox(
        request_id=request_id,
        variables=_heat_index_variables(solar_load),
        start_date=start_date,
        end_date=end_date,
        north=north,
        south=south,
        east=east,
        west=west,
        frequency="monthly",
        resolution=resolution,
        verbosity=verbosity,
        save_raw=False,
    )

    return _apply_heat_index_calculations(df, solar_load)


def get_era5_daily_heat_index_geojson(
    request_id: str,
    start_date: str,
    end_date: str,
    geojson_file: str,
    dist_features: Optional[List[str]] = None,
    solar_load: bool = False,
    resolution: float = 0.25,
    verbosity: int = 0,
) -> pd.DataFrame:
    """
    Download ERA5 daily data for a GeoJSON region and calculate heat stress indices.

    Args:
        request_id: Unique identifier for the request
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        geojson_file: Path to GeoJSON file defining the region
        dist_features: List of GeoJSON properties to distinguish features
        solar_load: If True, also download solar radiation for outdoor UTCI
        resolution: Spatial resolution in degrees (default 0.25)
        verbosity: Logging verbosity level (0-2)

    Returns:
        DataFrame with heat stress indices for points within the GeoJSON region
    """
    df = era5ify_geojson(
        request_id=request_id,
        variables=_heat_index_variables(solar_load),
        start_date=start_date,
        end_date=end_date,
        json_file=geojson_file,
        dist_features=dist_features,
        frequency="daily",
        resolution=resolution,
        verbosity=verbosity,
        save_raw=False,
    )

    return _apply_heat_index_calculations(df, solar_load)


def get_era5_daily_heat_index_point(
    request_id: str,
    start_date: str,
    end_date: str,
    latitude: float,
    longitude: float,
    solar_load: bool = False,
    verbosity: int = 0,
) -> pd.DataFrame:
    """
    Download ERA5 daily data for a single point and calculate heat stress indices.

    Args:
        request_id: Unique identifier for the request
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        latitude: Latitude of the point
        longitude: Longitude of the point
        solar_load: If True, also download solar radiation for outdoor UTCI
        verbosity: Logging verbosity level (0-2)

    Returns:
        DataFrame with heat stress indices for the specified point
    """
    df = era5ify_point(
        request_id=request_id,
        variables=_heat_index_variables(solar_load),
        start_date=start_date,
        end_date=end_date,
        latitude=latitude,
        longitude=longitude,
        frequency="daily",
        verbosity=verbosity,
        save_raw=False,
    )

    return _apply_heat_index_calculations(df, solar_load)
