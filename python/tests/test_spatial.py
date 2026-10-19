"""Tests for spatial.aggregate_to_polygons ``by=`` and ``fill_empty=``."""

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from varunayan.spatial import aggregate_to_polygons


def _cells() -> pd.DataFrame:
    rows = []
    for date in ("2020-01-01", "2020-01-02"):
        for lat in (0.0, 1.0):
            for lon in (0.0, 1.0, 2.0):
                rows.append(
                    {
                        "date": date,
                        "latitude": lat,
                        "longitude": lon,
                        "temp": lat * 10 + lon + (100 if date == "2020-01-02" else 0),
                    }
                )
    return pd.DataFrame(rows)


def _polys() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"name": ["left", "right", "tiny"]},
        geometry=[
            box(-0.5, -0.5, 1.5, 1.5),  # 4 cells: (0,0) (0,1) (1,0) (1,1)
            box(1.5, -0.5, 2.5, 0.5),  # 1 cell: (0, 2)
            box(1.8, 0.8, 1.9, 0.9),  # no cell; nearest is (1, 2)
        ],
        crs="EPSG:4326",
    )


def test_by_gives_one_row_per_polygon_and_group():
    out = aggregate_to_polygons(
        _cells(), _polys(), "temp", polygon_id_col="name", by="date"
    )
    covered = out.dropna(subset=["temp"])
    assert len(covered) == 4  # left/right x 2 dates
    got = {(r["name"], r["date"]): r["temp"] for _, r in covered.iterrows()}
    # left: mean of 0, 1, 10, 11 = 5.5
    assert got[("left", "2020-01-01")] == pytest.approx(5.5)
    assert got[("left", "2020-01-02")] == pytest.approx(105.5)
    assert got[("right", "2020-01-01")] == pytest.approx(2.0)
    assert got[("right", "2020-01-02")] == pytest.approx(102.0)


def test_without_fill_empty_tiny_polygon_is_nan():
    out = aggregate_to_polygons(
        _cells(), _polys(), "temp", polygon_id_col="name", by=["date"]
    )
    tiny = out[out["name"] == "tiny"]
    assert len(tiny) == 1
    assert np.isnan(tiny["temp"].iloc[0])


def test_fill_empty_uses_nearest_cell():
    out = aggregate_to_polygons(
        _cells(),
        _polys(),
        "temp",
        polygon_id_col="name",
        by="date",
        fill_empty=True,
    )
    assert not out["temp"].isna().any()
    assert len(out) == 6
    tiny = out[out["name"] == "tiny"].sort_values("date")
    # Nearest cell to (0.85, 1.85) is (1, 2): 10 + 2
    assert list(tiny["temp"]) == pytest.approx([12.0, 112.0])
    # fill_empty does not change covered polygons
    left = out[out["name"] == "left"].sort_values("date")
    assert list(left["temp"]) == pytest.approx([5.5, 105.5])


def test_no_by_aggregates_over_all_rows():
    out = aggregate_to_polygons(
        _cells(), _polys(), "temp", polygon_id_col="name", fill_empty=True
    )
    vals = dict(zip(out["name"], out["temp"]))
    assert vals["left"] == pytest.approx((5.5 + 105.5) / 2)
    assert vals["right"] == pytest.approx(52.0)
    assert vals["tiny"] == pytest.approx(62.0)


def test_agg_func_and_multiple_values():
    data = _cells()
    data["rain"] = data["temp"] * 2
    out = aggregate_to_polygons(
        data,
        _polys().iloc[:1],
        ["temp", "rain"],
        polygon_id_col="name",
        agg_func="max",
        by="date",
    )
    row = out[out["date"] == "2020-01-01"].iloc[0]
    assert row["temp"] == pytest.approx(11.0)
    assert row["rain"] == pytest.approx(22.0)


def test_default_polygon_id_from_index():
    out = aggregate_to_polygons(_cells(), _polys(), "temp", by="date")
    assert "_polygon_id" in out.columns
    assert set(out["_polygon_id"]) == {0, 1, 2}
