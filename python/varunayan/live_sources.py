"""METAR airport observations and Open-Meteo model weather. Neither needs a key."""

from __future__ import annotations

import gzip
import io
from typing import Any, Dict, Optional, Sequence

import pandas as pd
import requests

from .heat_stress import relative_humidity_from_dewpoint

METAR_BULK_URL = "https://aviationweather.gov/data/cache/metars.cache.csv.gz"
OPEN_METEO_CURRENT_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
_UA = "varunayan-cli"
_KNOTS_TO_MS = 0.514444
_OPEN_METEO_FIELDS = {
    "temperature_2m": "temperature",
    "relative_humidity_2m": "humidity",
    "wind_speed_10m": "wind_speed",
    "wind_direction_10m": "wind_direction",
    "precipitation": "rainfall",
}


def _request_json(url: str, params: Dict[str, Any], timeout: int) -> Any:
    resp = requests.get(
        url, params=params, headers={"User-Agent": _UA}, timeout=timeout
    )
    resp.raise_for_status()
    return resp.json()


def _parse_metar(text: str, prefixes: Optional[Sequence[str]]) -> pd.DataFrame:
    lines = text.splitlines()
    start = next((i for i, x in enumerate(lines) if x.startswith("raw_text")), None)
    if start is None:
        raise ValueError("The METAR file has no header line")
    raw = pd.read_csv(
        io.StringIO("\n".join(lines[start:])),
        usecols=[
            "raw_text",
            "station_id",
            "observation_time",
            "latitude",
            "longitude",
            "temp_c",
            "dewpoint_c",
            "wind_dir_degrees",
            "wind_speed_kt",
        ],
    )
    if prefixes:
        raw = raw[raw["station_id"].str.startswith(tuple(prefixes))]
    return pd.DataFrame(
        {
            "station_id": raw["station_id"],
            "observed_at": pd.to_datetime(raw["observation_time"].str[:19], utc=True),
            "latitude": raw["latitude"],
            "longitude": raw["longitude"],
            "temperature": raw["temp_c"],
            "dewpoint": raw["dewpoint_c"],
            "humidity": relative_humidity_from_dewpoint(
                raw["temp_c"], raw["dewpoint_c"]
            ),
            "wind_speed": raw["wind_speed_kt"] * _KNOTS_TO_MS,
            "wind_direction": pd.to_numeric(raw["wind_dir_degrees"], errors="coerce"),
            "raw_text": raw["raw_text"],
        }
    ).reset_index(drop=True)


def get_metar_observations(
    prefixes: Optional[Sequence[str]] = None, timeout: int = 60
) -> pd.DataFrame:
    """Return the latest METAR report from each airport.

    One request fetches every airport, from the NOAA Aviation Weather Center
    bulk file.

    Args:
        prefixes: keep airports whose ICAO code starts with one of these, for
            example ``("VA", "VE", "VI", "VO")`` for India. Default: every
            airport in the world.
        timeout: request timeout in seconds.

    Returns:
        DataFrame with one row per airport: ``station_id``, ``observed_at``
        (UTC), ``latitude``, ``longitude``, ``temperature`` (°C), ``dewpoint``
        (°C), ``humidity`` (%), ``wind_speed`` (m/s), ``wind_direction``
        (degrees, missing when variable) and ``raw_text``.
    """
    resp = requests.get(METAR_BULK_URL, headers={"User-Agent": _UA}, timeout=timeout)
    resp.raise_for_status()
    body = resp.content
    if body[:2] == b"\x1f\x8b":
        body = gzip.decompress(body)
    return _parse_metar(body.decode("utf-8", "replace"), prefixes)


def _parse_open_meteo(
    block: Dict[str, Any], latitude: float, longitude: float
) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "datetime": pd.to_datetime(block["time"], utc=True),
            "latitude": latitude,
            "longitude": longitude,
        }
    )
    for source, column in _OPEN_METEO_FIELDS.items():
        frame[column] = pd.to_numeric(pd.Series(block.get(source)), errors="coerce")
    if "interval" in block:  # current rainfall is mm per interval
        frame["rainfall"] *= 3600 / block["interval"][0]
    return frame


def get_open_meteo_weather(
    latitude: float,
    longitude: float,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    timeout: int = 30,
) -> pd.DataFrame:
    """Return Open-Meteo weather for a point: current, or hourly history.

    These are model values, not measurements.

    Args:
        latitude: latitude of the point.
        longitude: longitude of the point.
        start_date: first day of hourly history (YYYY-MM-DD). Give both dates
            or neither. With neither, the result is the current conditions.
        end_date: last day of hourly history (YYYY-MM-DD).
        timeout: request timeout in seconds.

    Returns:
        DataFrame with ``datetime`` (UTC), ``latitude``, ``longitude``,
        ``temperature`` (°C), ``humidity`` (%), ``wind_speed`` (m/s),
        ``wind_direction`` (degrees) and ``rainfall`` (mm/h).

    Raises:
        ValueError: if only one date is given.
    """
    if (start_date is None) != (end_date is None):
        raise ValueError("Give both start_date and end_date, or neither")
    fields = ",".join(_OPEN_METEO_FIELDS)
    params: Dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "wind_speed_unit": "ms",
        "timezone": "UTC",
    }
    current = start_date is None
    if current:
        url = OPEN_METEO_CURRENT_URL
        params["current"] = fields
    else:
        url = OPEN_METEO_ARCHIVE_URL
        params.update(hourly=fields, start_date=start_date, end_date=end_date)

    payload = _request_json(url, params, timeout)
    block = (
        {key: [value] for key, value in payload["current"].items()}
        if current
        else payload["hourly"]
    )
    return _parse_open_meteo(block, latitude, longitude)
