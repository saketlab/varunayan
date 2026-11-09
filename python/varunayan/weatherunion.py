"""Zomato Weather Union station list and current observations."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from importlib.resources import files
from typing import Iterable, Optional, Union

import pandas as pd
import requests

API_URL = (
    "https://www.weatherunion.com/gw/weather/external/v0/get_locality_weather_data"
)
API_KEY_ENV = "WEATHERUNION_API_KEY"
_FIELDS = [
    "temperature",
    "humidity",
    "wind_speed",
    "wind_direction",
    "rain_intensity",
    "rain_accumulation",
]


def get_weatherunion_stations(temperature_only: bool = False) -> pd.DataFrame:
    """Return the Weather Union stations bundled with the package.

    Args:
        temperature_only: if True, keep only automated weather stations. Rain
            gauges report rainfall alone, so temperature and humidity are
            always missing for them.

    Returns:
        DataFrame with columns ``station_id``, ``city``, ``name``,
        ``latitude``, ``longitude`` and ``device_type`` (``"aws"`` or
        ``"rain_gauge"``).
    """
    path = files("varunayan") / "data" / "weatherunion_stations.csv"
    with path.open("r", encoding="utf-8") as handle:
        raw = pd.read_csv(handle)
    stations = pd.DataFrame(
        {
            "station_id": raw["localityId"],
            "city": raw["cityName"],
            "name": raw["localityName"],
            "latitude": raw["latitude"],
            "longitude": raw["longitude"],
            "device_type": [
                "aws" if str(d).startswith("1") else "rain_gauge"
                for d in raw["device_type"]
            ],
        }
    )
    if temperature_only:
        stations = stations[stations["device_type"] == "aws"].reset_index(drop=True)
    return stations


def get_weatherunion_weather(
    station_ids: Union[str, Iterable[str]],
    api_key: Optional[str] = None,
    timeout: int = 30,
) -> pd.DataFrame:
    """Return current observations for Weather Union stations.

    Each station costs one request against the API key's daily quota. The API
    gives no observation time, so ``fetched_at`` is the UTC time of the request.

    Args:
        station_ids: one station id or several, from
            :func:`get_weatherunion_stations`.
        api_key: API key. Defaults to the ``WEATHERUNION_API_KEY`` environment
            variable.
        timeout: request timeout in seconds.

    Returns:
        DataFrame with one row per station: ``station_id``, ``fetched_at``,
        ``temperature`` (°C), ``humidity`` (%), ``wind_speed`` (m/s),
        ``wind_direction`` (degrees), ``rain_intensity`` (mm/min) and
        ``rain_accumulation`` (mm since 12 AM IST).

    Raises:
        ValueError: if no API key is available or the API reports a failure.
        requests.HTTPError: on an HTTP error, including 401 and 429.
    """
    key = api_key or os.environ.get(API_KEY_ENV)
    if not key:
        raise ValueError(f"Set {API_KEY_ENV} or pass api_key")

    ids = [station_ids] if isinstance(station_ids, str) else list(station_ids)
    rows = []
    for station_id in ids:
        resp = requests.get(
            API_URL,
            params={"locality_id": station_id},
            headers={"x-zomato-api-key": key},
            timeout=timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
        if str(payload.get("status")) != "200":  # the API sends "200" as a string
            raise ValueError(f"{station_id}: {payload.get('message')}")
        data = payload.get("locality_weather_data") or {}
        rows.append(
            {
                "station_id": station_id,
                "fetched_at": datetime.now(timezone.utc),
                **{field: data.get(field) for field in _FIELDS},
            }
        )
    return pd.DataFrame(rows, columns=["station_id", "fetched_at", *_FIELDS])
