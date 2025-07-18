import logging

import numpy as np
import pandas as pd
from typing import List
from ..util.logging_utils import get_logger
from .variable_lists import exclude_cols, max_vars, min_vars, rate_vars, sum_vars

logger = get_logger(level=logging.INFO)

#pyright: reportUnknownMemberType=false
def aggregate_by_frequency(
    df: pd.DataFrame, frequency: str, keep_original_time: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aggregate ERA5 data by the specified frequency for multiple points within a polygon.

    The function first aggregates data spatially (across points) for each timestamp,
    then performs temporal aggregation based on the specified frequency.

    Parameters:
        df: DataFrame containing ERA5 data with latitude/longitude points and timestamps
        frequency: One of 'hourly', 'daily', 'weekly', 'monthly', 'yearly'
        keep_original_time: Whether to keep the original valid_time column (default: False)

    Returns:
        Tuple of (aggregated DataFrame, unique lat/lon DataFrame)
    """
    logger.info(f"Aggregating data to {frequency} frequency...")

    frequency = frequency.lower()

    # Store unique lat/lon pairs for reference (not used in aggregation)
    unique_latlongs = (
        df[["latitude", "longitude"]].drop_duplicates().reset_index(drop=True)
    )

    # Ensure time column is properly formatted
    if "valid_time" in df.columns:
        if not np.issubdtype(df["valid_time"].dtype, np.datetime64):    #type: ignore
            df["valid_time"] = pd.to_datetime(df["valid_time"], errors="coerce")
        df["date"] = df["valid_time"].dt.date
        df["hour"] = df["valid_time"].dt.hour
        time_col = "valid_time"
    else:
        # If no valid_time, assume date and time columns exist
        if "date" not in df.columns or "time" not in df.columns:
            logger.warning(
                "Warning: No proper time columns found in DataFrame. Skipping aggregation."
            )
            return df, unique_latlongs

        # Convert date and time to datetime if needed
        if not isinstance(df["date"].iloc[0], pd.Timestamp):
            df["date"] = pd.to_datetime(df["date"])

        if isinstance(df["time"].iloc[0], str):
            df["hour"] = pd.to_datetime(df["time"]).dt.hour
        else:
            df["hour"] = df["time"].apply(lambda t: t.hour) #type: ignore

        # Create valid_time column for resampling
        df["valid_time"] = pd.to_datetime(df["date"]) + pd.to_timedelta(
            df["hour"], unit="h"
        )
        time_col = "valid_time"

    # Improved column matching for different categories
    var_cols = [col for col in df.columns if col not in exclude_cols]

    # Match columns that should be summed (more flexible matching)
    sum_cols : List[str] = []
    for col in var_cols:
        col_lower = col.lower()
        if any(sv == col_lower or sv in col_lower.split("_") for sv in sum_vars):
            sum_cols.append(col)

    # Match columns that should use max
    max_cols : List[str] = []
    for col in var_cols:
        col_lower = col.lower()
        if any(mv == col_lower or mv in col_lower.split("_") for mv in max_vars):
            max_cols.append(col)

    # Match columns that should use min
    min_cols : List[str] = []
    for col in var_cols:
        col_lower = col.lower()
        if any(mv == col_lower or mv in col_lower.split("_") for mv in min_vars):
            min_cols.append(col)

    # Match rate columns
    rate_cols : List[str] = []
    for col in var_cols:
        col_lower = col.lower()
        if any(rv == col_lower or rv in col_lower.split("_") for rv in rate_vars):
            rate_cols.append(col)

    # Average columns are those not covered by other aggregation methods
    special_cols = sum_cols + max_cols + min_cols + rate_cols
    avg_cols = [col for col in var_cols if col not in special_cols]

    logger.info(f"Sum columns: {sum_cols}")
    logger.info(f"Max columns: {max_cols}")
    logger.info(f"Min columns: {min_cols}")
    logger.info(f"Rate columns: {rate_cols}")
    logger.info(f"Average columns: {avg_cols}")

    # Return original data if hourly frequency requested
    if frequency == "hourly":
        # For hourly, just aggregate across spatial points for each hour
        spatial_agg = df.groupby([time_col], as_index=False).agg(
            {
                **{col: "mean" for col in avg_cols},
                **{
                    col: "mean" for col in sum_cols
                },  # Even sum vars are averaged spatially
                **{
                    col: "max" for col in max_cols
                },  # Max vars take maximum across points
                **{
                    col: "min" for col in min_cols
                },  # Min vars take minimum across points
                **{
                    col: "mean" for col in rate_cols
                },  # Rate vars are averaged spatially
            }
        )

        # Add standardized date columns for hourly frequency
        spatial_agg["date"] = spatial_agg[time_col].dt.date
        spatial_agg["year"] = spatial_agg[time_col].dt.year
        spatial_agg["month"] = spatial_agg[time_col].dt.month
        spatial_agg["day"] = spatial_agg[time_col].dt.day
        spatial_agg["hour"] = spatial_agg[time_col].dt.hour

        # Drop the original time column if requested
        if not keep_original_time:
            spatial_agg = spatial_agg.drop(columns=[time_col])

        return spatial_agg, unique_latlongs

    # Define frequency mapping for pandas resampling
    freq_map = {
        "daily": "D",  # Calendar day
        "weekly": "W",  # Weekly
        "monthly": "MS",  # Month start
        "yearly": "AS",  # Year start
    }

    if frequency not in freq_map and frequency != "hourly":
        raise ValueError(
            f"Invalid frequency: {frequency}. Must be one of {list(freq_map.keys()) + ['hourly']}"
        )

    # Step 1: First spatial aggregation - aggregate across points for each timestamp
    # Different aggregation methods based on variable type
    spatial_agg = df.groupby([time_col], as_index=False).agg(
        {
            **{col: "mean" for col in avg_cols},
            **{col: "mean" for col in sum_cols},  # Even sum vars are averaged spatially
            **{col: "max" for col in max_cols},  # Max vars take maximum across points
            **{col: "min" for col in min_cols},  # Min vars take minimum across points
            **{col: "mean" for col in rate_cols},  # Rate vars are averaged spatially
        }
    )

    # Step 2: Temporal aggregation based on the specified frequency
    # Set the datetime as index for resampling
    spatial_agg = spatial_agg.set_index(time_col)
    # Perform temporal aggregation
    result = pd.DataFrame()

    # For sum variables, sum over time periods
    for col in sum_cols:
        if col in spatial_agg.columns:
            result[col] = spatial_agg[col].resample(freq_map[frequency]).sum()

    # For max variables, take maximum over time periods
    for col in max_cols:
        if col in spatial_agg.columns:
            result[col] = spatial_agg[col].resample(freq_map[frequency]).max()

    # For min variables, take minimum over time periods
    for col in min_cols:
        if col in spatial_agg.columns:
            result[col] = spatial_agg[col].resample(freq_map[frequency]).min()

    # For rate variables, average over time periods (they're already rates)
    for col in rate_cols:
        if col in spatial_agg.columns:
            result[col] = spatial_agg[col].resample(freq_map[frequency]).mean()

    # For average variables, average over time periods
    for col in avg_cols:
        if col in spatial_agg.columns:
            result[col] = spatial_agg[col].resample(freq_map[frequency]).mean()

    # Reset index to get the datetime as a column
    result = result.reset_index()

    # Create standardized date columns based on frequency
    result["year"] = result[time_col].dt.year

    if frequency == "daily":
        result["month"] = result[time_col].dt.month
        result["day"] = result[time_col].dt.day
        result["date"] = result[time_col].dt.date
    elif frequency == "weekly":
        result["week"] = result[time_col].dt.isocalendar().week
    elif frequency == "monthly":
        result["month"] = result[time_col].dt.month

    # Drop the original time column if requested
    if not keep_original_time:
        result = result.drop(columns=[time_col])

    return result, unique_latlongs

#pyright: reportUnknownMemberType=false
def aggregate_pressure_levels(
    df: pd.DataFrame, frequency: str = "hourly", keep_original_time: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aggregate ERA5 pressure level data by the specified frequency.

    All variables are aggregated using mean values (both spatially and temporally).

    Parameters:
        df: DataFrame containing ERA5 pressure level data with columns:
            - latitude, longitude: Spatial coordinates
            - valid_time or time: Timestamps
            - pressure_level: Pressure level in hPa
            - Other columns: Meteorological variables
        frequency: One of 'hourly', 'daily', 'weekly', 'monthly', 'yearly'
        keep_original_time: Whether to keep the original time column

    Returns:
        Tuple of (aggregated DataFrame, unique lat/lon DataFrame)
    """
    logger.info(f"Aggregating pressure level data to {frequency} frequency...")

    # Store unique lat/lon pairs for reference
    unique_latlongs = (
        df[["latitude", "longitude"]].drop_duplicates().reset_index(drop=True)
    )

    # Identify time column (handle both valid_time and time)
    time_col = "valid_time" if "valid_time" in df.columns else "time"

    # Ensure time column is properly formatted
    if not np.issubdtype(df[time_col].dtype, np.datetime64):    #type: ignore
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

    # Identify pressure level column if exists
    has_pressure_level = "pressure_level" in df.columns

    # Grouping columns - always include time, optionally include pressure_level
    group_cols = [time_col]
    if has_pressure_level:
        group_cols.append("pressure_level")

    # Columns to exclude from aggregation
    exclude_cols = {
        "latitude",
        "longitude",
        "date",
        "time",
        "hour",
        "expver",
        "number",
        "valid_time",
    }

    # All other columns are variables to be averaged
    var_cols = [
        col for col in df.columns if col not in exclude_cols and col not in group_cols
    ]

    logger.info(f"Variables to average: {var_cols}")
    if has_pressure_level:
        logger.info("Including pressure_level in aggregation groups")

    # For hourly data, just do spatial aggregation
    if frequency == "hourly":
        # Group by time (and pressure level if present) and average across space
        agg_df = df.groupby(group_cols, as_index=False)[var_cols].mean()

        # Add time components
        agg_df["year"] = agg_df[time_col].dt.year
        agg_df["month"] = agg_df[time_col].dt.month
        agg_df["day"] = agg_df[time_col].dt.day
        agg_df["hour"] = agg_df[time_col].dt.hour

        if not keep_original_time:
            agg_df = agg_df.drop(columns=[time_col])

        return agg_df, unique_latlongs

    # For other frequencies, first spatial then temporal aggregation

    # 1. Spatial aggregation - average across lat/lon points
    spatial_agg = df.groupby(group_cols, as_index=False)[var_cols].mean()

    # 2. Temporal aggregation
    freq_map = {"daily": "D", "weekly": "W", "monthly": "MS", "yearly": "AS"}

    if frequency not in freq_map:
        raise ValueError(f"Invalid frequency: {frequency}")

    # Set time as index for resampling
    temporal_agg = spatial_agg.set_index(time_col)

    # For pressure levels, we need to group by pressure level before resampling
    if has_pressure_level:
        # Get unique pressure levels
        pressure_levels = df["pressure_level"].unique() #type: ignore

        # Initialize empty DataFrame for results
        result_df = pd.DataFrame()

        # Process each pressure level separately
        for level in pressure_levels:
            # Filter data for this pressure level
            level_data = temporal_agg[temporal_agg["pressure_level"] == level]  #type: ignore

            # Resample and average variables
            resampled = level_data[var_cols].resample(freq_map[frequency]).mean()   #type: ignore

            # Add pressure level back
            resampled["pressure_level"] = level

            # Combine results
            result_df = pd.concat([result_df, resampled.reset_index()]) #type: ignore
    else:
        # No pressure levels - simple resample
        result_df = (
            temporal_agg[var_cols].resample(freq_map[frequency]).mean().reset_index()
        )

    # Add frequency-specific time components
    result_df["year"] = result_df[time_col].dt.year

    if frequency == "daily":
        result_df["month"] = result_df[time_col].dt.month
        result_df["day"] = result_df[time_col].dt.day
    elif frequency == "weekly":
        result_df["week"] = result_df[time_col].dt.isocalendar().week
    elif frequency == "monthly":
        result_df["month"] = result_df[time_col].dt.month

    if not keep_original_time:
        result_df = result_df.drop(columns=[time_col])

    return result_df, unique_latlongs
