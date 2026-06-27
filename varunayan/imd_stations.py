"""IMD station registry with coordinates.
Example
-------
>>> import varunayan
>>> stations = varunayan.get_imd_stations()
>>> row = stations[stations["name"].str.contains("Shimla")].iloc[0]
>>> varunayan.era5ify_point("shimla", ["2t"], "2024-01-01", "2024-01-07",
...                         latitude=row.latitude, longitude=row.longitude)
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple

import pandas as pd
import requests

CITY_LIST_URL = "https://internal.imd.gov.in/pages/city_weather_main_mausam.php"
CITY_STATIC_API_URL = (
    "https://city.imd.gov.in/citywx/responsive/api/fetchCity_static.php"
)
CITY_STATIC_REFERER = "https://city.imd.gov.in/citywx/responsive/"
_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
_OPTION_RE = re.compile(r"<option value='(\d{4,6})([^']*)'>")
_INDIA_BBOX = (6.0, 38.0, 67.0, 99.0)


def _fetch_station_list(timeout: int = 30) -> pd.DataFrame:
    resp = requests.get(
        CITY_LIST_URL,
        headers={"User-Agent": _UA},
        timeout=timeout,
        verify=False,  # nosec B501
    )
    resp.raise_for_status()
    rows = [
        {"station_id": int(sid), "name": name.strip().title()}
        for sid, name in _OPTION_RE.findall(resp.text)
    ]
    return pd.DataFrame(rows).drop_duplicates("station_id").reset_index(drop=True)


def _fetch_coord(station_id: int, timeout: int = 30) -> Optional[Tuple[float, float]]:
    try:
        resp = requests.post(
            CITY_STATIC_API_URL,
            data={"ID": station_id},
            headers={"User-Agent": _UA, "Referer": CITY_STATIC_REFERER},
            timeout=timeout,
            verify=False,  # nosec B501
        )
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError):
        return None
    rec = payload[0] if isinstance(payload, list) and payload else payload
    if not isinstance(rec, dict):
        return None
    try:
        lat = float(str(rec.get("lat")))
        lon = float(str(rec.get("lon")))
    except (TypeError, ValueError):
        return None
    lat_min, lat_max, lon_min, lon_max = _INDIA_BBOX
    if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
        return None
    return (lat, lon)


def get_imd_stations(
    with_coordinates: bool = True, max_workers: int = 8
) -> pd.DataFrame:
    """Return IMD observation stations, optionally with coordinates.

    Args:
        with_coordinates: if True, fetch ``latitude``/``longitude`` per station
            (concurrent requests to IMD). If False, return only id + name.
        max_workers: concurrent requests when resolving coordinates.

    Returns:
        DataFrame with columns ``station_id``, ``name`` and — when
        ``with_coordinates`` — ``latitude``, ``longitude`` (NaN where IMD has
        no coordinate for a station).
    """
    stations = _fetch_station_list()
    if not with_coordinates:
        return stations

    ids = stations["station_id"].tolist()
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        coords = list(ex.map(_fetch_coord, ids))
    stations = stations.copy()
    stations["latitude"] = [c[0] if c else None for c in coords]
    stations["longitude"] = [c[1] if c else None for c in coords]
    return stations
