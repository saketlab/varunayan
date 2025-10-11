import logging
from typing import Any, List, Optional

import numpy as np
import pandas as pd

from ..util.logging_utils import get_logger
from .variable_lists import exclude_cols, max_vars, min_vars, rate_vars, sum_vars

logger = get_logger(level=logging.DEBUG)


def set_v_data_agg(verbosity: int) -> None:

    if verbosity == 0:
        logger.setLevel(logging.WARNING)

    elif verbosity == 1:
        logger.setLevel(logging.INFO)

    elif verbosity == 2:
        logger.setLevel(logging.DEBUG)

    else:
        logger.setLevel(logging.WARNING)


# pyright: reportUnknownMemberType=false
def aggregate_by_frequency(
    df: pd.DataFrame,
    frequency: str,
    keep_original_time: bool = False,
    dist_features: Optional[List[str]] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aggregate ERA5 data by the specified frequency for multiple points within a polygon.

    The function first aggregates data spatially (across points) for each timestamp,
    then performs temporal aggregation based on the specified frequency.

    If a 'feature' column is present, aggregation is performed separately for each feature.

    Parameters:
        df: DataFrame containing ERA5 data with latitude/longitude points and timestamps
        frequency: One of 'hourly', 'daily', 'weekly', 'monthly', 'yearly'
        keep_original_time: Whether to keep the original valid_time column (default: False)

    Returns:
        Tuple of (aggregated DataFrame, unique lat/lon DataFrame)
    """
    logger.info(f"Aggregating data to {frequency} frequency...")

    frequency = frequency.lower()

    # Check if feature column exists
    has_features = "feature" in df.columns
    if has_features:
        logger.info(
            "Feature column detected - performing separate aggregation for each feature"
        )
        features_array = df["feature"].dropna().unique()
        features: List[Any] = (
            features_array.tolist()
            if hasattr(features_array, "tolist")
            else list(features_array)
        )
        logger.info(f"Found {len(features)} unique features: {features}")

    # Store unique lat/lon pairs for reference (not used in aggregation)
    unique_latlongs = (
        df[["latitude", "longitude"]].drop_duplicates().reset_index(drop=True)
    )

    # Ensure time column is properly formatted
    if "valid_time" in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df["valid_time"]):
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

        time_series = pd.to_datetime(df["time"], errors="coerce")
        df["hour"] = time_series.dt.hour

        # Create valid_time column for resampling
        df["valid_time"] = pd.to_datetime(df["date"]) + pd.to_timedelta(
            df["hour"], unit="h"
        )
        time_col = "valid_time"

    # Improved column matching for different categories
    var_cols = [
        col for col in df.columns if col not in exclude_cols and col != "feature"
    ]

    # Match columns that should be summed (more flexible matching)
    sum_cols: List[str] = []
    for col in var_cols:
        col_lower = col.lower()
        if any(sv == col_lower or sv in col_lower.split("_") for sv in sum_vars):
            sum_cols.append(col)

    # Match columns that should use max
    max_cols: List[str] = []
    for col in var_cols:
        col_lower = col.lower()
        if any(mv == col_lower or mv in col_lower.split("_") for mv in max_vars):
            max_cols.append(col)

    # Match columns that should use min
    min_cols: List[str] = []
    for col in var_cols:
        col_lower = col.lower()
        if any(mv == col_lower or mv in col_lower.split("_") for mv in min_vars):
            min_cols.append(col)

    # Match rate columns
    rate_cols: List[str] = []
    for col in var_cols:
        col_lower = col.lower()
        if any(rv == col_lower or rv in col_lower.split("_") for rv in rate_vars):
            rate_cols.append(col)

    # Average columns are those not covered by other aggregation methods
    # Ensure dist_features is a list for safe concatenation
    dist_features = dist_features if isinstance(dist_features, list) else []
    special_cols = sum_cols + max_cols + min_cols + rate_cols + dist_features
    avg_cols = [col for col in var_cols if col not in special_cols]

    logger.debug(f"Sum columns: {sum_cols}")
    logger.debug(f"Max columns: {max_cols}")
    logger.debug(f"Min columns: {min_cols}")
    logger.debug(f"Rate columns: {rate_cols}")
    logger.debug(f"Average columns: {avg_cols}")

    if has_features:
        # Process each feature separately
        feature_results: List[pd.DataFrame] = []

        for feature in features:
            logger.debug(f"Processing feature: {feature}")
            feature_df = df[df["feature"] == feature].copy()

            # Process this feature using the same logic as the original function
            result_df = _process_single_feature(
                feature_df,
                frequency,
                time_col,
                sum_cols,
                max_cols,
                min_cols,
                rate_cols,
                avg_cols,
                keep_original_time,
            )

            # Add feature identifier back to results
            result_df["feature"] = feature
            feature_results.append(result_df)

        # Combine all feature results
        final_result = pd.concat(feature_results, ignore_index=True)

    else:
        # Original behavior - no features
        final_result = _process_single_feature(
            df,
            frequency,
            time_col,
            sum_cols,
            max_cols,
            min_cols,
            rate_cols,
            avg_cols,
            keep_original_time,
        )

    return final_result, unique_latlongs


def _process_single_feature(
    df: pd.DataFrame,
    frequency: str,
    time_col: str,
    sum_cols: List[str],
    max_cols: List[str],
    min_cols: List[str],
    rate_cols: List[str],
    avg_cols: List[str],
    keep_original_time: bool,
) -> pd.DataFrame:
    """
    Helper function to process aggregation for a single feature or the entire dataset.
    """
    # Return original data if hourly frequency requested
    if frequency == "hourly":
        # For hourly, just aggregate across spatial points for each hour
        spatial_agg = df.groupby([time_col], as_index=False).agg(
            {
                **{col: "mean" for col in avg_cols},
                **{col: "mean" for col in sum_cols},  # Sum vars are averaged spatially
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

        return spatial_agg

    # Define frequency mapping for pandas resampling
    freq_map = {
        "daily": "D",  # Calendar day
        "weekly": "W",  # Weekly
        "monthly": "MS",  # Month start
        "yearly": "YS",  # Year start
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

    return result


# pyright: reportUnknownMemberType=false
def aggregate_pressure_levels(
    df: pd.DataFrame,
    frequency: str = "hourly",
    keep_original_time: bool = False,
    dist_features: Optional[List[str]] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aggregate ERA5 pressure level data by the specified frequency.

    All variables are aggregated using mean values (both spatially and temporally).

    If a 'feature' column is present, aggregation is performed separately for each feature.

    Parameters:
        df: DataFrame containing ERA5 pressure level data with columns:
            - latitude, longitude: Spatial coordinates
            - valid_time or time: Timestamps
            - pressure_level: Pressure level in hPa
            - feature (optional): Feature identifier
            - Other columns: Meteorological variables
        frequency: One of 'hourly', 'daily', 'weekly', 'monthly', 'yearly'
        keep_original_time: Whether to keep the original time column

    Returns:
        Tuple of (aggregated DataFrame, unique lat/lon DataFrame)
    """
    logger.info(f"Aggregating pressure level data to {frequency} frequency...")

    # Check if feature column exists
    has_features = "feature" in df.columns
    if has_features:
        logger.info(
            "Feature column detected - performing separate aggregation for each feature"
        )
        features_array = df["feature"].dropna().unique()
        features: List[Any] = (
            features_array.tolist()
            if hasattr(features_array, "tolist")
            else list(features_array)
        )
        logger.info(f"Found {len(features)} unique features: {features}")

    # Store unique lat/lon pairs for reference
    unique_latlongs = (
        df[["latitude", "longitude"]].drop_duplicates().reset_index(drop=True)
    )

    # Identify time column (handle both valid_time and time)
    time_col = "valid_time" if "valid_time" in df.columns else "time"

    # Ensure time column is properly formatted
    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

    # Identify pressure level column if exists
    has_pressure_level = "pressure_level" in df.columns

    if has_features:
        # Process each feature separately
        feature_results: List[pd.DataFrame] = []

        for feature in features:
            logger.debug(f"Processing pressure level data for feature: {feature}")
            feature_df = df[df["feature"] == feature].copy()

            # Process this feature using the same logic as the original function
            result_df = _process_pressure_levels_single_feature(
                feature_df,
                frequency,
                time_col,
                has_pressure_level,
                keep_original_time,
            )

            # Add feature identifier back to results
            result_df["feature"] = feature
            feature_results.append(result_df)

        # Combine all feature results
        final_result = pd.concat(feature_results, ignore_index=True)

    else:
        # Original behavior - no features
        final_result = _process_pressure_levels_single_feature(
            df,
            frequency,
            time_col,
            has_pressure_level,
            keep_original_time,
            dist_features,
        )

    return final_result, unique_latlongs


def _process_pressure_levels_single_feature(
    df: pd.DataFrame,
    frequency: str,
    time_col: str,
    has_pressure_level: bool,
    keep_original_time: bool,
    dist_features: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Helper function to process pressure level aggregation for a single feature or the entire dataset.
    """
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
        "feature",  # Exclude feature column from aggregation variables
    }

    exclude_cols = (
        exclude_cols.union(set(dist_features)) if dist_features else exclude_cols
    )

    # All other columns are variables to be averaged
    var_cols = [
        col for col in df.columns if col not in exclude_cols and col not in group_cols
    ]

    logger.debug(f"Variables to average: {var_cols}")
    if has_pressure_level:
        logger.debug("Including pressure_level in aggregation groups")

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

        return agg_df

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
        pressure_levels_array = df["pressure_level"].dropna().unique()
        pressure_levels: List[Any] = (
            pressure_levels_array.tolist()
            if hasattr(pressure_levels_array, "tolist")
            else list(pressure_levels_array)
        )

        level_frames: List[pd.DataFrame] = []

        # Process each pressure level separately
        for level in pressure_levels:
            # Filter data for this pressure level
            level_data = temporal_agg[temporal_agg["pressure_level"] == level]

            # Resample and average variables
            resampled = (
                level_data[var_cols].resample(freq_map[frequency]).mean().reset_index()
            )

            # Add pressure level back
            resampled["pressure_level"] = level
            level_frames.append(resampled)

        result_df = pd.concat(level_frames, ignore_index=True)
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

    return result_df
