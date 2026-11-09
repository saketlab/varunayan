from unittest.mock import MagicMock, patch

import pytest

from varunayan import get_weatherunion_stations, get_weatherunion_weather


def test_temperature_only_drops_rain_gauges():
    all_stations = get_weatherunion_stations()
    aws = get_weatherunion_stations(temperature_only=True)
    assert set(all_stations["device_type"]) == {"aws", "rain_gauge"}
    assert set(aws["device_type"]) == {"aws"}
    assert 0 < len(aws) < len(all_stations)


@patch("varunayan.weatherunion.requests.get")
def test_weather_sends_one_request_per_station(get):
    get.return_value = MagicMock(
        json=lambda: {
            "status": "200",
            "message": "",
            "device_type": 1,
            "locality_weather_data": {"temperature": 25.68, "humidity": 25.81},
        }
    )
    df = get_weatherunion_weather(["A", "B"], api_key="k")
    assert get.call_count == 2
    assert get.call_args.kwargs["headers"] == {"x-zomato-api-key": "k"}
    assert list(df["station_id"]) == ["A", "B"]
    assert df["temperature"].tolist() == [25.68, 25.68]
    assert df["rain_intensity"].isna().all()


def test_weather_needs_a_key(monkeypatch):
    monkeypatch.delenv("WEATHERUNION_API_KEY", raising=False)
    with pytest.raises(ValueError, match="WEATHERUNION_API_KEY"):
        get_weatherunion_weather("A")
