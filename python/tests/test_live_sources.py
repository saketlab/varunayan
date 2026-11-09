import gzip
from unittest.mock import MagicMock, patch

import pytest

from varunayan import get_metar_observations, get_open_meteo_weather

METAR = (
    "raw_text,station_id,observation_time,latitude,longitude,temp_c,dewpoint_c,"
    "wind_dir_degrees,wind_speed_kt\n"
    "VABB 1,VABB,2026-11-09T09:00:00Z,19.1,72.8,30,20,VRB,10\n"
    "KJFK 1,KJFK,2026-11-09T09:00:00Z,40.6,-73.8,10,5,100,5\n"
)


@patch("varunayan.live_sources.requests.get")
def test_metar_reads_gzip_keeps_prefixes_and_converts(get):
    get.return_value = MagicMock(content=gzip.compress(METAR.encode()))
    out = get_metar_observations(["VA"])
    assert out["station_id"].tolist() == ["VABB"]
    assert out["wind_speed"].iloc[0] == pytest.approx(5.14444)
    assert out["wind_direction"].isna().all()
    assert 50 < out["humidity"].iloc[0] < 60
    assert str(out["observed_at"].iloc[0]) == "2026-11-09 09:00:00+00:00"


@patch("varunayan.live_sources.requests.get")
def test_open_meteo_history_uses_the_archive_and_keeps_gaps(get):
    get.return_value = MagicMock(
        json=lambda: {
            "hourly": {
                "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
                "temperature_2m": [10.0, None],
            }
        }
    )
    out = get_open_meteo_weather(19, 72, "2024-01-01", "2024-01-01")
    assert "archive-api" in get.call_args.args[0]
    assert len(out) == 2
    assert out["temperature"].isna().tolist() == [False, True]
    assert out["humidity"].isna().all()


@patch("varunayan.live_sources.requests.get")
def test_open_meteo_current_is_one_row(get):
    get.return_value = MagicMock(
        json=lambda: {"current": {"time": "2026-11-09T09:15", "temperature_2m": 35.8}}
    )
    out = get_open_meteo_weather(19, 72)
    assert out["temperature"].tolist() == [35.8]


def test_open_meteo_needs_both_dates():
    with pytest.raises(ValueError, match="both"):
        get_open_meteo_weather(1, 2, start_date="2024-01-01")
