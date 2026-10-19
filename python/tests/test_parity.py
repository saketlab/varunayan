"""Run parity/cases.json; R's test-parity.R runs the same cases."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pytest

import varunayan
from varunayan.processing.grid_output import to_long_grid

CASES = Path(__file__).resolve().parents[2] / "parity" / "cases.json"

if not CASES.exists():
    pytest.skip("shared parity cases not found", allow_module_level=True)

ALL_CASES: List[Dict[str, Any]] = json.loads(CASES.read_text())


def _nan(values: List[Any]) -> List[Any]:
    return [np.nan if v is None else v for v in values]


def _era5_grid_output(data: pd.DataFrame, frequency: str, convert_units: bool) -> Any:
    # R era5_grid_output() takes the long grid; Python to_long_grid() takes the
    # wide grid from the NetCDF file.
    keys = [
        c for c in ("datetime", "latitude", "longitude", "pressure_level") if c in data
    ]
    wide = data.pivot_table(
        index=keys, columns="variable", values="value", aggfunc="first", dropna=False
    ).reset_index()
    wide.columns.name = None
    wide = wide.rename(columns={"datetime": "valid_time"})
    wide["valid_time"] = pd.to_datetime(wide["valid_time"])
    return to_long_grid(wide, frequency, convert_units)


def _run(case: Dict[str, Any]) -> Any:
    if case["function"] == "era5_grid_output":
        data = pd.DataFrame({k: _nan(v) for k, v in case["data"].items()})
        return _era5_grid_output(data, **case["args"])
    fn = getattr(varunayan, case["function"])
    args = dict(case["args"])
    if "baseline" in args and args["baseline"] is not None:
        args["baseline"] = tuple(args["baseline"])
    if "data" in case:
        data = pd.DataFrame({k: _nan(v) for k, v in case["data"].items()})
        return fn(data, **args)
    return fn(
        **{k: np.asarray(v) if isinstance(v, list) else v for k, v in args.items()}
    )


@pytest.mark.parametrize("case", ALL_CASES, ids=[c["name"] for c in ALL_CASES])
def test_parity_case(case: Dict[str, Any]) -> None:
    result = _run(case)
    expected = case["expected"]
    tol = case["tol"]
    if isinstance(expected, dict):
        assert list(result.columns) == list(expected), "column names or order differ"
        assert len(result) == len(next(iter(expected.values())))
        for col, values in expected.items():
            got = result[col].to_numpy()
            if col == "date":
                assert list(result[col].dt.strftime("%Y-%m-%d")) == values
            elif col == "datetime":
                got_dt = list(result[col].dt.strftime("%Y-%m-%d %H:%M:%S"))
                assert got_dt == values
            elif isinstance(values[0], str):
                assert list(got) == values, col
            else:
                np.testing.assert_allclose(
                    got.astype(float),
                    np.array(_nan(values), dtype=float),
                    rtol=tol,
                    atol=tol,
                    err_msg=col,
                )
    elif isinstance(expected[0], str):
        assert [str(v) for v in np.asarray(result)] == expected
    else:
        np.testing.assert_allclose(
            np.asarray(result, dtype=float),
            np.array(_nan(expected), dtype=float),
            rtol=tol,
            atol=tol,
        )


def test_cases_cover_every_function() -> None:
    covered = {c["function"] for c in ALL_CASES}
    assert covered == {
        "spatial_mean",
        "compare",
        "cross_correlation",
        "anomaly",
        "seasonal_cycle",
        "peak_month",
        "seasonal_stat",
        "regrid",
        "dewpoint_from_relative_humidity",
        "era5_grid_output",
        "relative_humidity_from_dewpoint",
        "vapor_pressure_from_dewpoint",
        "wet_bulb_temperature",
        "wet_bulb_from_dewpoint",
        "heat_index",
        "heat_index_from_dewpoint",
        "humidex",
        "wbgt_simple",
        "wbgt_shade",
        "heat_index_risk_category",
        "wbgt_risk_category",
        "utci_category",
        "utci",
        "mean_radiant_temperature",
        "calc_heat_indices",
        "utci_sparse",
    }


PLOT_CASES: List[Dict[str, Any]] = json.loads(
    (CASES.parent / "plot_cases.json").read_text()
)


@pytest.mark.parametrize("case", PLOT_CASES, ids=[c["name"] for c in PLOT_CASES])
def test_parity_plot(case: Dict[str, Any]) -> None:
    from varunayan import plot

    args = dict(case["args"])
    if "ribbon" in args:
        args["ribbon"] = tuple(args["ribbon"])
    fig = getattr(plot, case["function"])(pd.DataFrame(case["data"]), **args)
    panels = [ax for ax in fig.axes if ax.get_label() != "<colorbar>"]
    n_panels = len({tuple(np.round(ax.get_position().bounds, 4)) for ax in panels})
    expected = case["expected"]
    assert n_panels == expected["n_panels"]
    title = fig._suptitle.get_text() if fig._suptitle else None
    assert title == expected["title"]
    if expected["ylabel"] is not None:
        assert panels[0].get_ylabel() == expected["ylabel"]


def test_version_matches_r() -> None:
    # Python and R share one version number; bump both together.
    description = Path(__file__).resolve().parents[2] / "R" / "DESCRIPTION"
    match = re.search(r"^Version:\s*(\S+)", description.read_text(), re.M)
    assert match and varunayan.__version__ == match.group(1)
