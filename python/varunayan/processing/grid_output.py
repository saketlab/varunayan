"""Convert the downloaded ERA5 grid to the long era5ify_* output, as in R."""

from typing import List

import pandas as pd

from .variable_lists import exclude_cols, get_aggregation_method, is_sum_var

TEMP_VARS = {
    "2m_temperature", "2m_dewpoint_temperature", "skin_temperature",
    "sea_surface_temperature", "soil_temperature_level_1",
    "soil_temperature_level_2", "soil_temperature_level_3",
    "soil_temperature_level_4", "temperature",
    "maximum_2m_temperature_since_previous_post_processing",
    "minimum_2m_temperature_since_previous_post_processing",
    "t2m", "d2m", "skt", "sst", "stl1", "stl2", "stl3", "stl4", "t",
    "mx2t", "mn2t",
}  # fmt: skip

PRECIP_VARS = {
    "total_precipitation", "convective_precipitation",
    "large_scale_precipitation", "snowfall", "total_evaporation", "evaporation",
    "tp", "cp", "lsp", "sf", "e",
}  # fmt: skip

_PERIODS = {"daily": "D", "weekly": "W-SUN", "monthly": "M", "yearly": "Y"}


def convert_era5_units(data: pd.DataFrame) -> pd.DataFrame:
    """Convert Kelvin to Celsius and metres to millimetres.

    Args:
        data: Long DataFrame with ``variable`` and ``value``.

    Returns:
        A copy with converted temperature and precipitation values.
    """
    out = data.copy()
    temp = out["variable"].isin(TEMP_VARS)
    precip = out["variable"].isin(PRECIP_VARS)
    out.loc[temp, "value"] = out.loc[temp, "value"] - 273.15
    out.loc[precip, "value"] = out.loc[precip, "value"] * 1000
    return out


def to_long_grid(
    df: pd.DataFrame, frequency: str, convert_units: bool = True
) -> pd.DataFrame:
    """Aggregate each grid cell in time and return the long output.

    The monthly-means product gives the mean daily value of an accumulated
    variable (for example precipitation). Such values are multiplied by the
    number of days in the month, so that monthly and yearly data are totals.

    Args:
        df: Wide grid from the NetCDF files (``valid_time``, ``latitude``,
            ``longitude``, optional ``pressure_level``, one column per variable).
        frequency: ``hourly``, ``daily``, ``weekly``, ``monthly`` or ``yearly``.
        convert_units: Convert to Celsius and millimetres.

    Returns:
        Long DataFrame sorted by time, latitude, longitude and variable.
    """
    keys = ["valid_time", "latitude", "longitude"]
    if "pressure_level" in df.columns:
        keys.append("pressure_level")
    var_cols = [c for c in df.columns if c not in exclude_cols and c not in keys]
    var_cols = [
        c for c in var_cols if c != "feature" and pd.api.types.is_numeric_dtype(df[c])
    ]

    long = df[keys + var_cols].melt(
        id_vars=keys, var_name="variable", value_name="value"
    )
    long["valid_time"] = pd.to_datetime(long["valid_time"])
    long["value"] = long["value"].astype("float64")

    if frequency in ("monthly", "yearly"):
        sums = long["variable"].map(is_sum_var).astype(bool)
        long.loc[sums, "value"] *= long.loc[sums, "valid_time"].dt.days_in_month

    if frequency != "hourly":
        if frequency not in _PERIODS:
            raise ValueError(f"Unknown frequency '{frequency}'")
        long["valid_time"] = (
            long["valid_time"].dt.to_period(_PERIODS[frequency]).dt.start_time
        )
        group = keys + ["variable"]
        parts: List[pd.DataFrame] = []
        for variable, part in long.groupby("variable", sort=False):
            how = get_aggregation_method(str(variable))
            grouped = part.groupby(group, as_index=False)[["value"]]
            # min_count=1: an all-missing group stays missing (as in R), not 0.
            parts.append(grouped.sum(min_count=1) if how == "sum" else grouped.agg(how))
        long = pd.concat(parts, ignore_index=True)

    long = long.rename(columns={"valid_time": "datetime"})
    if frequency in ("monthly", "yearly"):
        long["year"] = long["datetime"].dt.year
    if frequency == "monthly":
        long["month"] = long["datetime"].dt.month
    if convert_units:
        long = convert_era5_units(long)

    sort_cols = ["datetime", "latitude", "longitude"] + keys[3:] + ["variable"]
    return long.sort_values(sort_cols, ignore_index=True)
