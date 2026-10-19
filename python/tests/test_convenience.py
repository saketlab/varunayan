"""Tests for convenience._wide and the level pass-through of the wrappers."""

from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from varunayan.convenience import (
    _wide,
    get_era5_daily_heat_index_geojson,
    get_era5_daily_temperature,
)


def _long(variables: Dict[str, List[float]], extra: Dict[str, Any]) -> pd.DataFrame:
    """Long frame for two days at one cell; ``variables[v]`` gives one value per day."""
    rows = []
    for i, day in enumerate(("2020-01-01", "2020-01-02")):
        for var, vals in variables.items():
            row = {"datetime": pd.Timestamp(day), "variable": var, "value": vals[i]}
            row.update(extra)
            rows.append(row)
    return pd.DataFrame(rows)


def test_wide_one_column_per_variable():
    df = _long(
        {"t2m": [25.0, 26.0], "tp": [1.0, 0.0]},
        {"latitude": 10.0, "longitude": 20.0},
    )
    out = _wide(df)

    assert set(out.columns) == {"date", "latitude", "longitude", "t2m", "tp"}
    assert "datetime" not in out.columns
    assert out.columns.name is None
    assert len(out) == 2
    out = out.sort_values("date").reset_index(drop=True)
    assert list(out["date"]) == [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-02")]
    assert list(out["t2m"]) == [25.0, 26.0]
    assert list(out["tp"]) == [1.0, 0.0]


def test_wide_keeps_year_month_pressure_and_feature_columns():
    df = _long(
        {"t": [-5.0, -6.0]},
        {
            "latitude": 1.0,
            "longitude": 2.0,
            "pressure_level": 850,
            "year": 2020,
            "month": 1,
            "district": "D1",
        },
    )
    out = _wide(df)
    for col in ("pressure_level", "year", "month", "district", "t", "date"):
        assert col in out.columns
    assert list(out.sort_values("date")["t"]) == [-5.0, -6.0]


def test_wide_several_cells():
    rows = []
    for lat in (0.0, 0.25):
        for var in ("u10", "v10"):
            rows.append(
                {
                    "datetime": pd.Timestamp("2020-01-01"),
                    "latitude": lat,
                    "longitude": 5.0,
                    "variable": var,
                    "value": lat * 4 + (1 if var == "v10" else 0),
                }
            )
    out = _wide(pd.DataFrame(rows)).set_index("latitude")
    assert out.loc[0.0, "u10"] == 0.0
    assert out.loc[0.0, "v10"] == 1.0
    assert out.loc[0.25, "u10"] == 1.0
    assert out.loc[0.25, "v10"] == 2.0


def test_wide_missing_value_becomes_nan():
    df = pd.DataFrame(
        {
            "datetime": pd.to_datetime(["2020-01-01", "2020-01-01", "2020-01-02"]),
            "latitude": [0.0, 0.0, 0.0],
            "longitude": [0.0, 0.0, 0.0],
            "variable": ["t2m", "tp", "t2m"],
            "value": [1.0, 2.0, 3.0],
        }
    )
    out = _wide(df).sort_values("date").reset_index(drop=True)
    assert out.loc[0, "tp"] == 2.0
    assert np.isnan(out.loc[1, "tp"])


@patch("varunayan.convenience.era5ify_bbox")
def test_daily_temperature_renames(mock_bbox: MagicMock):
    mock_bbox.return_value = _long(
        {"t2m": [25.0, 27.0]}, {"latitude": 10.0, "longitude": 20.0}
    )
    out = get_era5_daily_temperature("r", "2020-01-01", "2020-01-02", 11, 9, 21, 19)
    assert mock_bbox.call_args.kwargs["frequency"] == "daily"
    assert "temp_c" in out.columns and "date" in out.columns
    assert list(out.sort_values("date")["temp_c"]) == [25.0, 27.0]


@pytest.mark.parametrize("level", ["union", "feature"])
@patch("varunayan.convenience.era5ify_geojson")
def test_heat_index_geojson_passes_level(mock_geojson: MagicMock, level: str):
    mock_geojson.return_value = _long(
        {
            "t2m": [30.0, 32.0],
            "d2m": [20.0, 21.0],
            "u10": [3.0, 0.0],
            "v10": [4.0, 1.0],
        },
        {"district": "D1"},
    )
    out = get_era5_daily_heat_index_geojson(
        "r", "2020-01-01", "2020-01-02", "x.geojson", level=level
    )
    kwargs = mock_geojson.call_args.kwargs
    assert kwargs["level"] == level
    assert "dist_features" not in kwargs
    assert kwargs["frequency"] == "daily"
    out = out.sort_values("date").reset_index(drop=True)
    assert list(out["temp_c"]) == [30.0, 32.0]
    assert list(out["dewpoint_c"]) == [20.0, 21.0]
    assert list(out["wind_speed"]) == pytest.approx([5.0, 1.0])
    assert "heat_index" in out.columns
