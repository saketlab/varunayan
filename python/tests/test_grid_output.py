"""Tests for to_long_grid and aggregate_to_features against hand-computed values."""

import calendar
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pytest

from varunayan.core import aggregate_to_features
from varunayan.processing.grid_output import (
    PRECIP_VARS,
    TEMP_VARS,
    convert_era5_units,
    to_long_grid,
)

K = 273.15


def _grid(times: List[str], cells: List[tuple], values: Dict[str, Any]) -> pd.DataFrame:
    """Wide grid like the NetCDF output.

    ``values[var]`` is a function ``(time_index, cell_index) -> value``.
    """
    rows = []
    for ti, t in enumerate(times):
        for ci, (lat, lon) in enumerate(cells):
            row: Dict[str, Any] = {
                "valid_time": pd.Timestamp(t),
                "latitude": lat,
                "longitude": lon,
            }
            for var, fn in values.items():
                row[var] = fn(ti, ci)
            rows.append(row)
    return pd.DataFrame(rows)


def _value(out: pd.DataFrame, **match: Any) -> float:
    mask = np.ones(len(out), dtype=bool)
    for col, val in match.items():
        if col == "datetime":
            val = pd.Timestamp(val)
        mask &= (out[col] == val).to_numpy()
    sel = out.loc[mask, "value"]
    assert len(sel) == 1, f"expected one row for {match}, got {len(sel)}"
    return float(sel.iloc[0])


# --------------------------------------------------------------------------
# Hourly
# --------------------------------------------------------------------------


def test_hourly_is_melt_without_aggregation():
    times = ["2020-01-01 00:00", "2020-01-01 01:00"]
    cells = [(20.0, 80.0), (20.25, 80.0)]
    df = _grid(
        times,
        cells,
        {"t2m": lambda t, c: 280.0 + t + 10 * c, "tp": lambda t, c: 0.001 * (t + 1)},
    )
    out = to_long_grid(df, "hourly", convert_units=False)

    assert list(out.columns) == [
        "datetime",
        "latitude",
        "longitude",
        "variable",
        "value",
    ]
    assert len(out) == 2 * 2 * 2
    assert _value(out, datetime=times[1], latitude=20.25, variable="t2m") == 291.0
    assert _value(out, datetime=times[1], latitude=20.0, variable="tp") == 0.002
    # tp is a sum variable but hourly data is not scaled
    assert out.loc[out["variable"] == "tp", "value"].max() == pytest.approx(0.002)


def test_hourly_sorted_by_time_lat_lon_variable():
    # Rows deliberately out of order
    df = pd.DataFrame(
        {
            "valid_time": pd.to_datetime(
                ["2020-01-01 01:00", "2020-01-01 00:00", "2020-01-01 00:00"]
            ),
            "latitude": [10.0, 10.5, 10.0],
            "longitude": [5.0, 5.0, 5.0],
            "u10": [1.0, 2.0, 3.0],
            "d2m": [4.0, 5.0, 6.0],
        }
    )
    out = to_long_grid(df, "hourly", convert_units=False)
    keys = list(
        zip(out["datetime"], out["latitude"], out["longitude"], out["variable"])
    )
    assert keys == sorted(keys)
    assert list(out.index) == list(range(len(out)))
    assert list(out["variable"][:2]) == ["d2m", "u10"]


def test_drops_excluded_and_non_numeric_columns():
    df = _grid(
        ["2020-01-01 00:00"],
        [(1.0, 2.0)],
        {
            "t2m": lambda t, c: 300.0,
            "number": lambda t, c: 0,
            "expver": lambda t, c: "0001",
            "feature": lambda t, c: 7,
            "label": lambda t, c: "x",
        },
    )
    out = to_long_grid(df, "hourly", convert_units=False)
    assert list(out["variable"]) == ["t2m"]


def test_input_not_mutated():
    df = _grid(
        ["2020-01-01", "2020-02-01"],
        [(1.0, 2.0)],
        {"tp": lambda t, c: 0.001, "t2m": lambda t, c: 300.0},
    )
    before = df.copy()
    to_long_grid(df, "monthly", convert_units=True)
    pd.testing.assert_frame_equal(df, before)


def test_unknown_frequency_raises():
    df = _grid(["2020-01-01"], [(1.0, 2.0)], {"t2m": lambda t, c: 300.0})
    with pytest.raises(ValueError, match="Unknown frequency"):
        to_long_grid(df, "fortnightly")


# --------------------------------------------------------------------------
# Daily: sum / max / min / mean per variable
# --------------------------------------------------------------------------


def _daily_input() -> pd.DataFrame:
    times = [f"2020-01-0{d} {h:02d}:00" for d in (1, 2) for h in (0, 6, 12, 18)]
    cells = [(20.0, 80.0), (20.0, 80.25)]
    return _grid(
        times,
        cells,
        {
            "tp": lambda t, c: 0.001 * (t + 1) * (c + 1),
            "mx2t": lambda t, c: 290.0 + (t * 7 % 5) + c,
            "mn2t": lambda t, c: 270.0 - (t * 3 % 4) - c,
            "t2m": lambda t, c: 280.0 + t + 2 * c,
        },
    )


def test_daily_aggregation_methods():
    df = _daily_input()
    out = to_long_grid(df, "daily", convert_units=False)

    assert list(out.columns) == [
        "datetime",
        "latitude",
        "longitude",
        "variable",
        "value",
    ]
    # 2 days x 2 cells x 4 variables
    assert len(out) == 16

    # Independent loop over the input
    for day in ("2020-01-01", "2020-01-02"):
        for lon in (80.0, 80.25):
            sub = df[(df["valid_time"].dt.strftime("%Y-%m-%d") == day)]
            sub = sub[sub["longitude"] == lon]
            tp_sum = 0.0
            mx = -np.inf
            mn = np.inf
            t_total = 0.0
            for _, r in sub.iterrows():
                tp_sum += r["tp"]
                mx = max(mx, r["mx2t"])
                mn = min(mn, r["mn2t"])
                t_total += r["t2m"]
            m = {"datetime": day, "longitude": lon}
            assert _value(out, variable="tp", **m) == pytest.approx(tp_sum)
            assert _value(out, variable="mx2t", **m) == pytest.approx(mx)
            assert _value(out, variable="mn2t", **m) == pytest.approx(mn)
            assert _value(out, variable="t2m", **m) == pytest.approx(t_total / 4)


def test_daily_datetime_is_midnight():
    out = to_long_grid(_daily_input(), "daily", convert_units=False)
    assert set(out["datetime"]) == {
        pd.Timestamp("2020-01-01"),
        pd.Timestamp("2020-01-02"),
    }


def test_daily_by_hand_values():
    # Day 1, cell 0: tp = 0.001 * (1+2+3+4) = 0.010, t2m mean = 281.5
    out = to_long_grid(_daily_input(), "daily", convert_units=False)
    m = {"datetime": "2020-01-01", "longitude": 80.0}
    assert _value(out, variable="tp", **m) == pytest.approx(0.010)
    assert _value(out, variable="t2m", **m) == pytest.approx(281.5)
    # mx2t over t = 0..3: 290 + [0, 2, 4, 1] -> 294
    assert _value(out, variable="mx2t", **m) == pytest.approx(294.0)
    # mn2t over t = 0..3: 270 - [0, 3, 2, 1] -> 267
    assert _value(out, variable="mn2t", **m) == pytest.approx(267.0)


def test_long_variable_names_use_same_methods():
    df = _grid(
        ["2020-01-01 00:00", "2020-01-01 12:00"],
        [(0.0, 0.0)],
        {
            "total_precipitation": lambda t, c: [0.002, 0.003][t],
            "10m_wind_gust": lambda t, c: [5.0, 9.0][t],
            "2m_temperature": lambda t, c: [280.0, 290.0][t],
        },
    )
    out = to_long_grid(df, "daily", convert_units=False)
    assert _value(out, variable="total_precipitation") == pytest.approx(0.005)
    assert _value(out, variable="10m_wind_gust") == pytest.approx(9.0)
    assert _value(out, variable="2m_temperature") == pytest.approx(285.0)


# --------------------------------------------------------------------------
# Weekly
# --------------------------------------------------------------------------


def test_weekly_starts_on_monday_and_aggregates():
    # 2020-01-01 is a Wednesday. Weeks: Mon 2019-12-30..Sun 2020-01-05 and
    # Mon 2020-01-06..Sun 2020-01-12.
    days = pd.date_range("2020-01-01", "2020-01-08", freq="D")
    df = _grid(
        [str(d) for d in days],
        [(0.0, 0.0)],
        {"tp": lambda t, c: 0.001 * (t + 1), "t2m": lambda t, c: 280.0 + t},
    )
    out = to_long_grid(df, "weekly", convert_units=False)

    assert set(out["datetime"]) == {
        pd.Timestamp("2019-12-30"),
        pd.Timestamp("2020-01-06"),
    }
    # Week 1 holds Jan 1-5 (t = 0..4); week 2 holds Jan 6-8 (t = 5..7)
    assert _value(out, datetime="2019-12-30", variable="tp") == pytest.approx(0.015)
    assert _value(out, datetime="2020-01-06", variable="tp") == pytest.approx(0.021)
    assert _value(out, datetime="2019-12-30", variable="t2m") == pytest.approx(282.0)
    assert _value(out, datetime="2020-01-06", variable="t2m") == pytest.approx(286.0)


# --------------------------------------------------------------------------
# Monthly and yearly: accumulated variables are totals
# --------------------------------------------------------------------------


def test_monthly_scales_sum_vars_by_days_in_month():
    # Monthly-means product: tp is the mean daily total (m/day)
    times = ["2020-01-01", "2020-02-01", "2021-02-01", "2021-04-01"]
    df = _grid(
        times,
        [(0.0, 0.0)],
        {"tp": lambda t, c: 0.002, "t2m": lambda t, c: 300.0, "mx2t": lambda t, c: 305},
    )
    out = to_long_grid(df, "monthly", convert_units=False)

    assert list(out.columns) == [
        "datetime",
        "latitude",
        "longitude",
        "variable",
        "value",
        "year",
        "month",
    ]
    days = {"2020-01-01": 31, "2020-02-01": 29, "2021-02-01": 28, "2021-04-01": 30}
    for t, n in days.items():
        assert _value(out, datetime=t, variable="tp") == pytest.approx(0.002 * n)
        # Non-accumulated variables are not scaled
        assert _value(out, datetime=t, variable="t2m") == pytest.approx(300.0)
        assert _value(out, datetime=t, variable="mx2t") == pytest.approx(305.0)

    feb_leap = out[(out["year"] == 2020) & (out["month"] == 2)]
    assert len(feb_leap) == 3
    assert list(out["year"]) == [pd.Timestamp(t).year for t in times for _ in "abc"]
    assert list(out["month"]) == [pd.Timestamp(t).month for t in times for _ in "abc"]


def test_monthly_precip_in_mm_with_units():
    df = _grid(
        ["2020-02-01"], [(0.0, 0.0)], {"total_precipitation": lambda t, c: 0.003}
    )
    out = to_long_grid(df, "monthly", convert_units=True)
    # 3 mm/day * 29 days
    assert _value(out, variable="total_precipitation") == pytest.approx(87.0)


@pytest.mark.parametrize("year", [2020, 2021])
def test_yearly_totals_and_means(year: int):
    months = [f"{year}-{m:02d}-01" for m in range(1, 13)]
    df = _grid(
        months,
        [(0.0, 0.0), (0.25, 0.0)],
        {
            "tp": lambda t, c: 0.001 * (c + 1),
            "t2m": lambda t, c: 270.0 + t,
            "mx2t": lambda t, c: 280.0 + (t * 5 % 12),
            "mn2t": lambda t, c: 260.0 - (t * 5 % 12),
        },
    )
    out = to_long_grid(df, "yearly", convert_units=False)

    assert list(out.columns) == [
        "datetime",
        "latitude",
        "longitude",
        "variable",
        "value",
        "year",
    ]
    assert set(out["datetime"]) == {pd.Timestamp(f"{year}-01-01")}
    assert set(out["year"]) == {year}

    ndays = 366 if calendar.isleap(year) else 365
    for c, lat in enumerate((0.0, 0.25)):
        total = 0.0
        for m in range(1, 13):
            total += 0.001 * (c + 1) * calendar.monthrange(year, m)[1]
        assert total == pytest.approx(0.001 * (c + 1) * ndays)
        assert _value(out, latitude=lat, variable="tp") == pytest.approx(total)
        assert _value(out, latitude=lat, variable="t2m") == pytest.approx(275.5)
        assert _value(out, latitude=lat, variable="mx2t") == pytest.approx(291.0)
        assert _value(out, latitude=lat, variable="mn2t") == pytest.approx(249.0)


# --------------------------------------------------------------------------
# Unit conversion
# --------------------------------------------------------------------------


def test_unit_conversion_on_and_off():
    df = _grid(
        ["2020-01-01 00:00"],
        [(0.0, 0.0)],
        {
            "t2m": lambda t, c: 300.0,
            "2m_dewpoint_temperature": lambda t, c: 290.0,
            "skt": lambda t, c: 280.0,
            "tp": lambda t, c: 0.004,
            "snowfall": lambda t, c: 0.0005,
            "u10": lambda t, c: 3.0,
            "sp": lambda t, c: 101325.0,
        },
    )
    on = to_long_grid(df, "hourly", convert_units=True)
    off = to_long_grid(df, "hourly", convert_units=False)

    assert _value(on, variable="t2m") == pytest.approx(300.0 - K)
    assert _value(on, variable="2m_dewpoint_temperature") == pytest.approx(290 - K)
    assert _value(on, variable="skt") == pytest.approx(280.0 - K)
    assert _value(on, variable="tp") == pytest.approx(4.0)
    assert _value(on, variable="snowfall") == pytest.approx(0.5)
    assert _value(on, variable="u10") == pytest.approx(3.0)
    assert _value(on, variable="sp") == pytest.approx(101325.0)

    assert _value(off, variable="t2m") == pytest.approx(300.0)
    assert _value(off, variable="tp") == pytest.approx(0.004)


def test_daily_conversion_after_aggregation():
    df = _grid(
        ["2020-01-01 00:00", "2020-01-01 12:00"],
        [(0.0, 0.0)],
        {"t2m": lambda t, c: [280.0, 290.0][t], "tp": lambda t, c: [0.001, 0.002][t]},
    )
    out = to_long_grid(df, "daily", convert_units=True)
    assert _value(out, variable="t2m") == pytest.approx(285.0 - K)
    assert _value(out, variable="tp") == pytest.approx(3.0)


def test_convert_era5_units_copy():
    data = pd.DataFrame({"variable": ["t2m", "tp", "u10"], "value": [K, 0.01, 1.0]})
    out = convert_era5_units(data)
    np.testing.assert_allclose(out["value"], [0.0, 10.0, 1.0])
    np.testing.assert_allclose(data["value"], [K, 0.01, 1.0])


def test_unit_sets_cover_short_and_long_names():
    assert {"t2m", "2m_temperature", "mx2t", "mn2t", "t"} <= TEMP_VARS
    assert {"tp", "total_precipitation", "e", "evaporation"} <= PRECIP_VARS
    assert not TEMP_VARS & PRECIP_VARS


# --------------------------------------------------------------------------
# Pressure levels
# --------------------------------------------------------------------------


def test_pressure_level_kept_and_sorted():
    rows = []
    for t in ("2020-01-01 00:00", "2020-01-01 12:00"):
        for lev in (850, 500):
            for lat in (10.25, 10.0):
                rows.append(
                    {
                        "valid_time": pd.Timestamp(t),
                        "pressure_level": lev,
                        "latitude": lat,
                        "longitude": 70.0,
                        "t": 250.0 + lev / 10 + (12 if t.endswith("12:00") else 0),
                        "r": 50.0 + lev / 100,
                    }
                )
    df = pd.DataFrame(rows)
    out = to_long_grid(df, "daily", convert_units=True)

    assert list(out.columns) == [
        "datetime",
        "latitude",
        "longitude",
        "pressure_level",
        "variable",
        "value",
    ]
    # 1 day x 2 lats x 2 levels x 2 variables
    assert len(out) == 8
    keys = list(
        zip(
            out["latitude"],
            out["longitude"],
            out["pressure_level"],
            out["variable"],
        )
    )
    assert keys == sorted(keys)
    assert list(out["pressure_level"][:4]) == [500, 500, 850, 850]

    # t at 850 hPa: mean of 335 and 347 = 341 K, then Celsius
    assert _value(
        out, latitude=10.0, pressure_level=850, variable="t"
    ) == pytest.approx(341.0 - K)
    assert _value(
        out, latitude=10.25, pressure_level=500, variable="r"
    ) == pytest.approx(55.0)


# --------------------------------------------------------------------------
# NaN handling
# --------------------------------------------------------------------------


def test_nan_values_skipped_in_aggregation():
    df = _grid(
        ["2020-01-01 00:00", "2020-01-01 06:00", "2020-01-01 12:00"],
        [(0.0, 0.0), (0.0, 0.25)],
        {
            "t2m": lambda t, c: [280.0, np.nan, 290.0][t],
            "tp": lambda t, c: [0.001, np.nan, 0.002][t],
            "mx2t": lambda t, c: [np.nan, 300.0, 299.0][t],
            # Ocean-only variable: NaN everywhere on the second cell
            "sst": lambda t, c: 295.0 if c == 0 else np.nan,
        },
    )
    out = to_long_grid(df, "daily", convert_units=False)
    m = {"longitude": 0.0}
    assert _value(out, variable="t2m", **m) == pytest.approx(285.0)
    assert _value(out, variable="tp", **m) == pytest.approx(0.003)
    assert _value(out, variable="mx2t", **m) == pytest.approx(300.0)
    assert _value(out, variable="sst", **m) == pytest.approx(295.0)
    # All-NaN group stays NaN (not 0)
    assert np.isnan(_value(out, variable="sst", longitude=0.25))


def test_nan_kept_in_hourly():
    df = _grid(
        ["2020-01-01 00:00"],
        [(0.0, 0.0)],
        {"t2m": lambda t, c: np.nan, "tp": lambda t, c: 0.001},
    )
    out = to_long_grid(df, "hourly", convert_units=True)
    assert len(out) == 2
    assert np.isnan(_value(out, variable="t2m"))
    assert _value(out, variable="tp") == pytest.approx(1.0)


# --------------------------------------------------------------------------
# aggregate_to_features
# --------------------------------------------------------------------------


def _box(west: float, south: float, east: float, north: float) -> Dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [
            [[west, south], [east, south], [east, north], [west, north], [west, south]]
        ],
    }


def _features() -> Dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"state": "S1", "district": "Big", "pop": 100},
                "geometry": _box(-0.1, -0.1, 0.6, 0.1),
            },
            {
                "type": "Feature",
                "properties": {"state": "S1", "district": "Tiny", "pop": 5},
                # Between grid points, nearest to (0.5, 0.5)
                "geometry": _box(0.44, 0.44, 0.46, 0.46),
            },
        ],
    }


def _long_cells() -> pd.DataFrame:
    # Cells on a 0.25 grid: lat 0 and 0.5, lon 0, 0.25, 0.5
    rows = []
    for day in ("2020-01-01", "2020-01-02"):
        for lat in (0.0, 0.5):
            for lon in (0.0, 0.25, 0.5):
                for var in ("t2m", "tp"):
                    rows.append(
                        {
                            "datetime": pd.Timestamp(day),
                            "latitude": lat,
                            "longitude": lon,
                            "variable": var,
                            "value": lat * 100 + lon * 10 + (1 if var == "tp" else 0),
                        }
                    )
    return pd.DataFrame(rows)


def test_aggregate_to_features_props_and_means():
    out = aggregate_to_features(_long_cells(), _features())

    assert {"state", "district", "pop", "datetime", "variable", "value"} == set(
        out.columns
    )
    assert "feature_id" not in out.columns
    # 2 features x 2 days x 2 variables
    assert len(out) == 8

    big = out[(out["district"] == "Big") & (out["variable"] == "t2m")]
    # Cells in Big: (0, 0), (0, 0.25), (0, 0.5) -> values 0, 2.5, 5
    assert list(big["value"]) == pytest.approx([2.5, 2.5])
    assert set(big["pop"]) == {100}
    assert set(big["state"]) == {"S1"}

    tiny = out[(out["district"] == "Tiny") & (out["variable"] == "tp")]
    # Nearest cell (0.5, 0.5): 50 + 5 + 1
    assert list(tiny["value"]) == pytest.approx([56.0, 56.0])
    assert set(tiny["pop"]) == {5}


def test_aggregate_to_features_keeps_year_month_and_level():
    data = _long_cells()
    data["pressure_level"] = 850
    data["year"] = data["datetime"].dt.year
    data["month"] = data["datetime"].dt.month
    out = aggregate_to_features(data, _features())
    for col in ("pressure_level", "year", "month", "datetime", "variable"):
        assert col in out.columns
    assert len(out) == 8
