"""Run parity/cases.json; R's test-parity.R runs the same cases."""

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

import varunayan
from varunayan import live_sources, live_weather
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


LIVE: Dict[str, Any] = json.loads((CASES.parent / "live_cases.json").read_text())


def _assert_close(got: Any, expected: List[Any], name: str) -> None:
    np.testing.assert_allclose(
        np.asarray(got, dtype=float),
        np.array(_nan(expected), dtype=float),
        rtol=1e-9,
        atol=1e-9,
        err_msg=name,
    )


def test_parity_metar_file() -> None:
    case = LIVE["metar_file"]
    out = live_sources._parse_metar(case["text"], case["prefixes"])
    assert out["station_id"].tolist() == case["expected"]["station_id"]
    times = out["observed_at"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
    assert times == case["expected"]["observed_at"]
    for column, values in case["expected"].items():
        if column not in ("station_id", "observed_at"):
            _assert_close(out[column], values, column)


@pytest.mark.parametrize("name", ["open_meteo", "open_meteo_current"])
def test_parity_open_meteo_block(name: str) -> None:
    case = LIVE[name]
    out = live_sources._parse_open_meteo(case["block"], 19.0, 72.0)
    for column, values in case["expected"].items():
        _assert_close(out[column], values, column)


@pytest.mark.parametrize("case", LIVE["metar_rain"], ids=lambda c: c["raw"])
def test_parity_metar_rain(case: Dict[str, Any]) -> None:
    assert live_weather._metar_reports_rain(case["raw"]) is case["rain"]


def test_parity_nearest_airport() -> None:
    case = LIVE["nearest_airport"]
    now = int(time.time())
    reports = [
        {
            **{k: v for k, v in r.items() if k != "age_minutes"},
            "obsTime": now - r["age_minutes"] * 60,
        }
        for r in case["reports"]
    ]
    with patch.object(live_weather, "_get_json", return_value=reports):
        got = live_weather._metar(live_weather.Place(**case["place"]))
    expected = case["expected"]
    assert got.site == expected["site"]
    for field in ("distance_km", "temperature", "humidity", "wind_speed"):
        _assert_close([getattr(got, field)], [expected[field]], field)
    assert got.wind_direction is None
    assert got.rain_reported is expected["rain_reported"]


HERE = live_weather.Place(19.0, 72.0, "Here")


@pytest.mark.parametrize("case", LIVE["openweathermap_rain"])
def test_parity_openweathermap_rain(
    case: Dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(live_weather.OPENWEATHERMAP_KEY_ENV, "k")
    with patch.object(live_weather, "_get_json", return_value=case["payload"]):
        got = live_weather._openweathermap(HERE)
    _assert_close([got.rainfall], [case["expected"]], "rainfall")


@pytest.mark.parametrize("case", LIVE["weatherunion_rain"])
def test_parity_weatherunion_rain(
    case: Dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(live_weather.API_KEY_ENV, "k")
    stations = pd.DataFrame(
        [
            {
                "station_id": "S1",
                "city": "C",
                "name": "N",
                "latitude": 19.0,
                "longitude": 72.0,
            }
        ]
    )
    weather = pd.DataFrame(
        [
            {
                "temperature": 30.0,
                "humidity": 50.0,
                "wind_speed": 1.0,
                "wind_direction": 10.0,
                "rain_intensity": case["rain_intensity"],
            }
        ]
    )
    with (
        patch.object(live_weather, "get_weatherunion_stations", return_value=stations),
        patch.object(live_weather, "get_weatherunion_weather", return_value=weather),
    ):
        got = live_weather._weatherunion(HERE)
    _assert_close([got.rainfall], [case["expected"]], "rainfall")


def test_parity_current_weather_columns() -> None:
    case = LIVE["current_weather"]
    frame = pd.DataFrame(
        [{"datetime": pd.Timestamp("2026-11-09 09:15", tz="UTC"), **case["row"]}]
    )
    with patch.object(live_weather, "get_open_meteo_weather", return_value=frame):
        out = live_weather.get_current_weather(
            latitude=19.0, longitude=72.0, source="open-meteo"
        )
    assert list(out.columns) == case["columns"]
    _assert_close(out["rainfall"], [case["row"]["rainfall"]], "rainfall")


def test_parity_place_names() -> None:
    case = LIVE["place_names"]
    hit = live_weather._choose_place(case["results"], case["query"])
    assert hit["name"] == case["expected"]


def test_station_lists_match_r() -> None:
    root = Path(__file__).resolve().parents[2]
    digests = {
        hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (
            root / "python" / "varunayan" / "data" / "weatherunion_stations.csv",
            root / "R" / "inst" / "extdata" / "weatherunion_stations.csv",
        )
    }
    assert len(digests) == 1


def test_parity_limits() -> None:
    limits = LIVE["limits"]
    assert live_weather._MAX_STATION_KM == limits["station_km"]
    assert live_weather._MAX_STATION_TRIES == limits["station_tries"]
    assert live_weather._MAX_AIRPORT_KM == limits["airport_km"]
    assert (
        live_weather._MAX_AIRPORT_AGE.total_seconds() / 60 == limits["airport_minutes"]
    )
    assert live_weather._HEAT_INDEX_MIN_C == limits["heat_index_min_c"]


def test_parity_metar_bbox() -> None:
    for case in LIVE["metar_bbox"]:
        place = live_weather.Place(case["latitude"], case["longitude"], "x")
        assert live_weather._metar_bbox(place) == case["expected"]
