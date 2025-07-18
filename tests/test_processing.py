from typing import Any, Dict

import numpy as np
import pandas as pd
import xarray as xr

# Adjust the import path according to your package structure
from varunayan.processing import (
    aggregate_by_frequency,
    aggregate_pressure_levels,
    filter_netcdf_by_shapefile,
)


def test_aggregate_by_frequency_hourly():
    """Test hourly aggregation (should return original data)"""
    df = pd.DataFrame(
        {
            "valid_time": pd.to_datetime(["2020-01-01 00:00", "2020-01-01 01:00"]),  # type: ignore
            "latitude": [37.5, 37.5],
            "longitude": [-122.5, -122.5],
            "t2m": [280, 281],
            "tp": [0, 0.1],
        }
    )

    result, unique_coords = aggregate_by_frequency(df, "hourly")
    assert len(result) == 2  # No aggregation for hourly
    assert "t2m" in result.columns
    assert "tp" in result.columns
    assert len(unique_coords) == 1  # Only one unique coordinate


def test_aggregate_by_frequency_daily():
    """Test daily aggregation of hourly data"""
    dates = pd.date_range("2020-01-01", "2020-01-02", freq="h")[:-1]
    df = pd.DataFrame(
        {
            "valid_time": dates,
            "latitude": [37.5] * len(dates),
            "longitude": [-122.5] * len(dates),
            "t2m": np.linspace(280, 282, len(dates)),
            "tp": np.linspace(0, 0.005, len(dates)),
        }
    )

    result, unique_coords = aggregate_by_frequency(df, "daily")  # type: ignore
    assert len(result) == 1  # Aggregated to 1 day
    assert "t2m" in result.columns
    assert "tp" in result.columns
    assert 280 < result["t2m"].iloc[0] < 282
    assert 0 < result["tp"].iloc[0] < 0.6


def test_aggregate_by_frequency_monthly():
    """Test monthly aggregation of daily data"""
    dates = pd.date_range("2020-01-01", "2020-01-31", freq="D")
    df = pd.DataFrame(
        {
            "valid_time": dates,
            "latitude": [37.5] * len(dates),
            "longitude": [-122.5] * len(dates),
            "t2m": np.linspace(280, 285, len(dates)),
            "tp": np.linspace(0, 3.0, len(dates)),
        }
    )

    result, unique_coords = aggregate_by_frequency(df, "monthly")  # type: ignore
    assert len(result) == 1  # Aggregated to 1 month
    assert "t2m" in result.columns
    assert "tp" in result.columns
    assert result["month"].iloc[0] == 1
    assert result["year"].iloc[0] == 2020


def test_aggregate_pressure_levels():
    """Test aggregation of pressure level data"""
    df = pd.DataFrame(
        {
            "valid_time": pd.to_datetime(["2020-01-01 00:00"] * 3),  # type: ignore
            "latitude": [37.5] * 3,
            "longitude": [-122.5] * 3,
            "pressure_level": [500, 850, 1000],
            "z": [5000, 1500, 100],
            "t": [250, 275, 290],
        }
    )

    result, _ = aggregate_pressure_levels(df, "hourly")
    assert len(result) == 3  # returns 3 time points, one for each pressure level
    assert result[result["pressure_level"] == 500]["z"].eq(5000).all()  # type: ignore


def test_filter_netcdf_by_shapefile(sample_geojson: Dict[str, Any]):
    """Test filtering NetCDF data by GeoJSON polygon"""
    # Create a mock xarray Dataset
    mock_ds = xr.Dataset(
        data_vars={
            "t2m": (
                ("time", "latitude", "longitude"),
                np.random.rand(2, 3, 3) * 10 + 280,
            )
        },
        coords={
            "time": pd.date_range("2020-01-01", periods=2),
            "latitude": [37.4, 37.5, 37.6],
            "longitude": [-122.6, -122.5, -122.4],
        },
    )

    # Test filtering - should keep points within the polygon
    result = filter_netcdf_by_shapefile(mock_ds, sample_geojson)
    assert len(result) > 0
    assert all(37.5 <= lat <= 38.0 for lat in result["latitude"])
    assert all(-122.5 <= lon <= -122.0 for lon in result["longitude"])
