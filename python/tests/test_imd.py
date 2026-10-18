"""IMD module: metadata, filters, aggregation, binary reader."""

import numpy as np
import pandas as pd
import pytest

from varunayan.imd import (
    IMD_GRID_SPECS,
    aggregate_imd_by_frequency,
    filter_imd_by_bbox,
    get_imd_grid_specs,
    list_imd_datasets,
    read_imd_temperature,
)


def test_grid_specs_keys():
    assert set(IMD_GRID_SPECS.keys()) == {
        "rainfall_0.25",
        "rainfall_1.0",
        "tmax_1.0",
        "tmin_1.0",
    }


def test_get_imd_grid_specs():
    s = get_imd_grid_specs("tmax_1.0")
    assert s["nlat"] == 31
    assert s["nlon"] == 31
    assert s["resolution"] == 1.0


def test_get_imd_grid_specs_invalid():
    with pytest.raises(ValueError, match="Unknown dataset"):
        get_imd_grid_specs("bogus")


def test_list_imd_datasets():
    df = list_imd_datasets()
    assert len(df) == 4
    assert list(df.columns) == [
        "dataset",
        "nlat",
        "nlon",
        "resolution",
        "unit",
        "format",
        "lat_range",
        "lon_range",
    ]
    assert set(df["dataset"]) == {
        "rainfall_0.25",
        "rainfall_1.0",
        "tmax_1.0",
        "tmin_1.0",
    }


def test_filter_imd_by_bbox():
    data = pd.DataFrame(
        {
            "latitude": [10, 20, 30, 40],
            "longitude": [70, 80, 90, 100],
            "temperature": [25, 30, 35, 40],
        }
    )
    result = filter_imd_by_bbox(data, north=35, south=15, east=95, west=75)
    assert len(result) == 2
    assert list(result["latitude"]) == [20, 30]


def test_aggregate_daily_noop():
    data = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=3),
            "latitude": [10, 10, 10],
            "longitude": [70, 70, 70],
            "temperature": [25, 30, 28],
        }
    )
    result = aggregate_imd_by_frequency(data, "daily")
    assert len(result) == 3


def test_aggregate_monthly_temperature():
    data = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=31),
            "latitude": [10] * 31,
            "longitude": [70] * 31,
            "temperature": [25.0] * 31,
        }
    )
    result = aggregate_imd_by_frequency(data, "monthly")
    assert len(result) == 1
    assert abs(result["temperature"].iloc[0] - 25.0) < 1e-10


def test_aggregate_monthly_rainfall_sums():
    data = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=31),
            "latitude": [10] * 31,
            "longitude": [70] * 31,
            "rainfall": [1.0] * 31,
        }
    )
    result = aggregate_imd_by_frequency(data, "monthly")
    assert len(result) == 1
    assert abs(result["rainfall"].iloc[0] - 31.0) < 1e-10


def test_read_imd_temperature_synthetic():
    import tempfile

    specs = IMD_GRID_SPECS["tmax_1.0"]
    year = 2023
    n_days = 365
    n_values = specs["nlon"] * specs["nlat"] * n_days
    values = np.full(n_values, 35.0, dtype="<f4")
    values[0] = 99.9
    with tempfile.NamedTemporaryFile(suffix=".grd", delete=False) as f:
        values.tofile(f)
        grd_file = f.name
    try:
        df = read_imd_temperature(grd_file, "tmax", year)
        assert "date" in df.columns
        assert "latitude" in df.columns
        assert "longitude" in df.columns
        assert "temperature" in df.columns
        assert (df["temperature"] < 99).all()
        assert abs(df["temperature"].iloc[0] - 35.0) < 1e-5
    finally:
        import os

        os.unlink(grd_file)
