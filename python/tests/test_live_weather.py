import json
import sys
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests
from rich.console import Console

from varunayan import cli, live_cli, live_weather
from varunayan.live_weather import Place, get_live_weather

MUMBAI = Place(19.09, 72.87, "Mumbai")
ZURICH = Place(47.37, 8.55, "Zurich")
OPEN_METEO = {
    "current": {
        "time": "2026-11-09T09:15",
        "temperature_2m": 12.5,
        "relative_humidity_2m": 60,
        "wind_speed_10m": 2.0,
        "wind_direction_10m": 80,
    }
}


def _reply(body):
    return MagicMock(json=lambda: body)


def _no_airports_then_model(url, **_):
    return _reply([] if "aviationweather" in url else OPEN_METEO)


@pytest.fixture(autouse=True)
def no_keys(monkeypatch):
    monkeypatch.delenv("WEATHERUNION_API_KEY", raising=False)
    monkeypatch.delenv("OPENWEATHERMAP_API_KEY", raising=False)


@patch("varunayan.live_weather.requests.get", side_effect=_no_airports_then_model)
def test_auto_says_why_each_source_was_passed(_):
    reading, skipped = get_live_weather(MUMBAI)
    assert reading.source == "open-meteo"
    assert reading.kind == "model"
    assert "WEATHERUNION_API_KEY is not set" in skipped["weatherunion"]
    assert "OPENWEATHERMAP_API_KEY is not set" in skipped["openweathermap"]
    assert "no recent airport" in skipped["metar"]


@patch("varunayan.live_weather.get_weatherunion_weather")
def test_weatherunion_uses_the_nearest_station(weather, monkeypatch):
    monkeypatch.setenv("WEATHERUNION_API_KEY", "k")
    weather.return_value = pd.DataFrame(
        [
            {
                "temperature": 30.0,
                "humidity": 50.0,
                "wind_speed": 1.0,
                "wind_direction": 10.0,
            }
        ]
    )
    reading, skipped = get_live_weather(MUMBAI)
    assert reading.source == "weatherunion"
    assert reading.kind == "station"
    assert reading.distance_km < 25
    assert skipped == {}
    weather.assert_called_once()


@patch("varunayan.live_weather.get_weatherunion_weather")
def test_weatherunion_tries_at_most_three_stations(weather, monkeypatch):
    monkeypatch.setenv("WEATHERUNION_API_KEY", "k")
    weather.return_value = pd.DataFrame(
        [
            {
                "temperature": None,
                "humidity": None,
                "wind_speed": None,
                "wind_direction": None,
            }
        ]
    )
    reading, skipped = get_live_weather(MUMBAI, "weatherunion")
    assert reading is None
    assert "nearest stations is reporting" in skipped["weatherunion"]
    assert weather.call_count == 3


@patch("varunayan.live_weather.get_weatherunion_weather")
@patch("varunayan.live_weather.requests.get", side_effect=_no_airports_then_model)
def test_outside_india_spends_no_weatherunion_quota(_, weather, monkeypatch):
    monkeypatch.setenv("WEATHERUNION_API_KEY", "k")
    reading, skipped = get_live_weather(ZURICH)
    assert reading.source == "open-meteo"
    assert "no station within" in skipped["weatherunion"]
    weather.assert_not_called()


@patch("varunayan.live_weather.requests.get")
def test_metar_converts_units_and_ignores_old_reports(get):
    now = int(time.time())
    get.return_value = _reply(
        [
            {
                "temp": 20,
                "dewp": 10,
                "obsTime": now - 90000,
                "lat": 19.09,
                "lon": 72.87,
            },
            {
                "temp": 30,
                "dewp": 20,
                "wspd": 10,
                "wdir": "VRB",
                "obsTime": now - 600,
                "lat": 19.2,
                "lon": 72.9,
                "icaoId": "VABB",
            },
        ]
    )
    reading, _ = get_live_weather(MUMBAI, "metar")
    assert reading.temperature == 30
    assert reading.wind_speed == pytest.approx(5.14444)
    assert reading.wind_direction is None
    assert 50 < reading.humidity < 60
    assert reading.observed_at > datetime.fromtimestamp(now - 700, timezone.utc)


@patch("varunayan.live_weather.requests.get")
def test_errors_never_reveal_an_api_key(get, monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "secret123")
    response = requests.Response()
    response.status_code = 401
    response.url = "https://x/?appid=secret123"
    get.return_value = response
    reading, skipped = get_live_weather(MUMBAI, "openweathermap")
    assert reading is None
    assert skipped == {"openweathermap": "HTTP 401"}


@patch("varunayan.live_weather.requests.get")
def test_metar_box_has_clean_coordinates(get):
    get.return_value = _reply([])
    with pytest.raises(live_weather.SourceUnavailable):
        live_weather._metar(Place(19.09, 72.87, "x"))
    assert get.call_args.kwargs["params"]["bbox"] == "18.64,72.39,19.54,73.35"


@patch("varunayan.live_weather._get_json")
@patch("varunayan.live_weather.get_metar_observations")
def test_explicit_metar_finds_a_far_airport_but_auto_does_not(bulk, get_json):
    now = pd.Timestamp.now(tz="UTC")
    get_json.side_effect = lambda url, params: (
        [{"name": f"{params['ids']} Arpt"}] if "ids" in params else []
    )
    bulk.return_value = pd.DataFrame(
        {
            "station_id": ["NEAR", "STALE", "FAR"],
            "observed_at": [now, now - pd.Timedelta(days=2), now],
            "latitude": [31.1, 31.1, 40.0],
            "longitude": [76.0, 77.2, 80.0],
            "temperature": [20.0, 5.0, 1.0],
            "humidity": [50.0, 50.0, 50.0],
            "wind_speed": [1.0, 1.0, 1.0],
            "wind_direction": [10.0, 10.0, 10.0],
        }
    )
    shimla = Place(31.1, 77.17, "Shimla")
    reading, _ = get_live_weather(shimla, "metar")
    assert reading.site == "NEAR Arpt"
    assert 100 < reading.distance_km < 120
    with pytest.raises(live_weather.SourceUnavailable):
        live_weather.SOURCES["metar"](shimla)


@patch("varunayan.live_weather.requests.get")
def test_place_name_prefers_an_exact_match(get):
    get.return_value = _reply(
        {
            "results": [
                {"name": "Le Havre", "latitude": 49.5, "longitude": 0.1},
                {
                    "name": "Leh",
                    "latitude": 34.2,
                    "longitude": 77.6,
                    "country": "India",
                },
            ]
        }
    )
    place = live_weather.locate("Leh", None, None)
    assert place.label == "Leh, India"
    assert place.latitude == 34.2


@patch("varunayan.live_cli.era5ify_point")
@patch("varunayan.live_weather.requests.get")
def test_historical_uses_ip_location_and_saves(get, era5, tmp_path, capsys):
    get.return_value = _reply({"loc": "19.09,72.87", "city": "Mumbai", "country": "IN"})
    era5.return_value = pd.DataFrame(
        {
            "datetime": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "latitude": [19.0, 19.0],
            "longitude": [73.0, 73.0],
            "variable": ["2m_temperature"] * 2,
            "value": [25.0, 26.0],
        }
    )
    out = tmp_path / "h.csv"
    argv = [
        "varunayan",
        "historical",
        "--start",
        "2024-01-01",
        "--end",
        "2024-01-02",
        "--path",
        str(out),
    ]
    with patch.object(sys, "argv", argv):
        cli.main()
    assert era5.call_args.kwargs["lat"] == 19.09
    assert era5.call_args.kwargs["frequency"] == "daily"
    assert "from IP" in capsys.readouterr().out
    assert len(pd.read_csv(out)) == 2


@patch("varunayan.live_cli.era5ify_point")
@patch("varunayan.live_weather.requests.get")
def test_open_meteo_history_needs_no_era5(get, era5, capsys):
    get.return_value = _reply(
        {"hourly": {"time": ["2024-01-01T00:00"], "temperature_2m": [20.0]}}
    )
    argv = [
        "varunayan",
        "historical",
        "--lat",
        "19",
        "--lon",
        "72",
        "--start",
        "2024-01-01",
        "--end",
        "2024-01-01",
        "--source",
        "open-meteo",
    ]
    with patch.object(sys, "argv", argv):
        cli.main()
    era5.assert_not_called()
    assert "open-meteo hourly" in capsys.readouterr().out


def test_open_meteo_history_rejects_other_frequencies():
    args = MagicMock(source="open-meteo", freq="daily", json=True, variables="x")
    assert live_cli.run_historical(args) == 1


@patch("varunayan.live_weather.requests.get", side_effect=_no_airports_then_model)
def test_cli_json_output(_, capsys):
    argv = ["varunayan", "live", "--lat", "19.09", "--lon", "72.87", "--json"]
    with patch.object(sys, "argv", argv):
        cli.main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["reading"]["temperature"] == 12.5
    assert payload["heat_index"] is None
    assert "weatherunion" in payload["skipped"]


@patch("varunayan.live_weather.requests.get", side_effect=_no_airports_then_model)
def test_cli_panel_labels_a_model_value(_, capsys):
    argv = ["varunayan", "live", "--lat", "19.09", "--lon", "72.87"]
    with patch.object(sys, "argv", argv):
        cli.main()
    assert "Model estimate" in capsys.readouterr().out


def test_panel_shows_weather_colors_rain_and_wind_icon():
    reading = live_weather.Reading(
        source="metar",
        kind="airport",
        site="Mumbai",
        distance_km=1.0,
        temperature=38.0,
        humidity=70.0,
        wind_speed=3.0,
        wind_direction=90.0,
        observed_at=None,
        rain_reported=True,
    )
    place = live_weather.Place(19.0, 72.0, "Mumbai")
    console = Console(record=True, width=80, force_terminal=True)
    live_cli._render(console, place, reading, {})
    text = console.export_text()
    assert "💨" in text and "Raining" in text and "70.0 %" in text
    assert "[red]38.0 °C" in live_cli._styled(38.0, "°C", live_cli._TEMPERATURE_BANDS)
    assert "[blue]5.0 °C" in live_cli._styled(5.0, "°C", live_cli._TEMPERATURE_BANDS)
    assert live_cli._styled(None, "°C", live_cli._TEMPERATURE_BANDS) == "[dim]n/a[/dim]"


def test_failure_exits_nonzero():
    args = MagicMock(place=None, lat=1.0, lon=1.0, source="metar", json=True)
    with patch.object(
        live_cli,
        "get_live_weather",
        return_value=(None, {"metar": "down"}),
    ):
        assert live_cli.run_live(args) == 1
