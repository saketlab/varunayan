"""Live weather for one place. Each reading says what it is and how old it is."""

from __future__ import annotations

import math
import os
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple, cast

import pandas as pd
import requests

from ._geo_utils import haversine_km
from .heat_stress import heat_index, relative_humidity_from_dewpoint
from .live_sources import (
    _KNOTS_TO_MS,
    _request_json,
    get_metar_observations,
    get_open_meteo_weather,
)
from .weatherunion import (
    API_KEY_ENV,
    get_weatherunion_stations,
    get_weatherunion_weather,
)

_TIMEOUT = 20
_MAX_STATION_KM = 25.0
_MAX_STATION_TRIES = 3  # each try costs one Weather Union request
METAR_URL = "https://aviationweather.gov/api/data/metar"
_MAX_AIRPORT_KM = 50.0
_MAX_AIRPORT_AGE = timedelta(minutes=90)
_HEAT_INDEX_MIN_C = 27.0
OPENWEATHERMAP_KEY_ENV = "OPENWEATHERMAP_API_KEY"


class SourceUnavailable(RuntimeError):
    """This source cannot answer for this place; the next one may."""


@dataclass(frozen=True)
class Place:
    latitude: float
    longitude: float
    label: str


@dataclass(frozen=True)
class Reading:
    source: str
    kind: str  # "station", "airport" or "model"
    site: str
    distance_km: Optional[float]
    temperature: Optional[float]
    humidity: Optional[float]
    wind_speed: Optional[float]
    wind_direction: Optional[float]
    observed_at: Optional[datetime]  # None when the source gives no time


@contextmanager
def _source_errors() -> Iterator[None]:
    """Reduce fetch errors to a reason; URLs can hold an API key."""
    try:
        yield
    except requests.HTTPError as err:
        code = err.response.status_code if err.response is not None else "error"
        raise SourceUnavailable(f"HTTP {code}") from None
    except (requests.RequestException, ValueError, KeyError) as err:
        raise SourceUnavailable(type(err).__name__) from None


def _nearest(place: Place, frame: pd.DataFrame, n: int = 1) -> pd.DataFrame:
    """The n rows closest to place, with their distance."""
    km = [
        haversine_km(place.latitude, place.longitude, lat, lon)
        for lat, lon in zip(frame["latitude"], frame["longitude"])
    ]
    return frame.assign(distance_km=km).nsmallest(n, "distance_km")


def _get_json(url: str, params: Dict[str, Any]) -> Any:
    with _source_errors():
        return _request_json(url, params, _TIMEOUT)


def _number(value: Any) -> Optional[float]:
    """Return value as a float, or None for gaps such as METAR's "VRB"."""
    try:
        return None if pd.isna(value) else float(value)
    except (TypeError, ValueError):
        return None


def _row_values(row: pd.Series) -> Dict[str, Optional[float]]:
    fields = ("temperature", "humidity", "wind_speed", "wind_direction")
    return {field: _number(row[field]) for field in fields}


def _weatherunion(place: Place) -> Reading:
    if not os.environ.get(API_KEY_ENV):
        raise SourceUnavailable(f"{API_KEY_ENV} is not set")
    stations = get_weatherunion_stations(temperature_only=True)
    nearby = _nearest(place, stations, _MAX_STATION_TRIES)
    nearby = nearby[nearby["distance_km"] <= _MAX_STATION_KM]
    if nearby.empty:
        raise SourceUnavailable(f"no station within {_MAX_STATION_KM:.0f} km")
    for _, station in nearby.iterrows():  # a listed station may report nothing
        with _source_errors():
            row = get_weatherunion_weather(
                station["station_id"], timeout=_TIMEOUT
            ).iloc[0]
        if _number(row["temperature"]) is None:
            continue
        return Reading(
            source="weatherunion",
            kind="station",
            site=f"{station['name']}, {station['city']}",
            distance_km=float(station["distance_km"]),
            observed_at=None,
            **_row_values(row),
        )
    raise SourceUnavailable(f"none of the {len(nearby)} nearest stations is reporting")


def _openweathermap(place: Place) -> Reading:
    key = os.environ.get(OPENWEATHERMAP_KEY_ENV)
    if not key:
        raise SourceUnavailable(f"{OPENWEATHERMAP_KEY_ENV} is not set")
    data = _get_json(
        "https://api.openweathermap.org/data/2.5/weather",
        {
            "lat": place.latitude,
            "lon": place.longitude,
            "units": "metric",
            "appid": key,
        },
    )
    main, wind = data.get("main", {}), data.get("wind", {})
    return Reading(
        source="openweathermap",
        kind="model",
        site=data.get("name") or place.label,
        distance_km=None,
        temperature=_number(main.get("temp")),
        humidity=_number(main.get("humidity")),
        wind_speed=_number(wind.get("speed")),
        wind_direction=_number(wind.get("deg")),
        observed_at=datetime.fromtimestamp(data["dt"], timezone.utc),
    )


def _metar_bbox(place: Place) -> str:
    """Box around the search circle; a degree of latitude is at least 110 km."""
    lat_box = _MAX_AIRPORT_KM / 110.0
    lon_box = lat_box / max(math.cos(math.radians(place.latitude)), 0.01)
    return (
        f"{place.latitude - lat_box:.2f},{place.longitude - lon_box:.2f},"
        f"{place.latitude + lat_box:.2f},{place.longitude + lon_box:.2f}"
    )


def _metar(place: Place) -> Reading:
    reports = _get_json(METAR_URL, {"bbox": _metar_bbox(place), "format": "json"})
    now = datetime.now(timezone.utc)
    usable: List[Tuple[float, Dict[str, Any], datetime]] = []
    for report in reports or []:
        if _number(report.get("temp")) is None or report.get("obsTime") is None:
            continue
        observed = datetime.fromtimestamp(report["obsTime"], timezone.utc)
        km = haversine_km(place.latitude, place.longitude, report["lat"], report["lon"])
        if km <= _MAX_AIRPORT_KM and now - observed <= _MAX_AIRPORT_AGE:
            usable.append((km, report, observed))
    if not usable:
        raise SourceUnavailable(
            f"no recent airport report within {_MAX_AIRPORT_KM:.0f} km"
        )

    km, report, observed = min(usable, key=lambda item: item[0])
    temperature = float(report["temp"])
    dewpoint = _number(report.get("dewp"))
    speed = _number(report.get("wspd"))
    return Reading(
        source="metar",
        kind="airport",
        site=report.get("name") or report.get("icaoId", "airport"),
        distance_km=km,
        temperature=temperature,
        humidity=(
            None
            if dewpoint is None
            else float(
                cast(float, relative_humidity_from_dewpoint(temperature, dewpoint))
            )
        ),
        wind_speed=None if speed is None else speed * _KNOTS_TO_MS,
        wind_direction=_number(report.get("wdir")),
        observed_at=observed,
    )


def _metar_any_distance(place: Place) -> Reading:
    """The closest fresh report in the world, for an explicit METAR request."""
    with _source_errors():
        reports = get_metar_observations()

    age = datetime.now(timezone.utc) - reports["observed_at"]
    fresh = reports[reports["temperature"].notna() & (age <= _MAX_AIRPORT_AGE)]
    if fresh.empty:
        raise SourceUnavailable("no recent airport report anywhere")
    row = _nearest(place, fresh).iloc[0]
    site = row["station_id"]
    try:  # the bulk file has only the ICAO code
        named = _get_json(METAR_URL, {"ids": site, "format": "json"})
        site = (named[0].get("name") if named else None) or site
    except SourceUnavailable:
        pass
    return Reading(
        source="metar",
        kind="airport",
        site=site,
        distance_km=float(row["distance_km"]),
        observed_at=row["observed_at"].to_pydatetime(),
        **_row_values(row),
    )


def _metar_nearest(place: Place) -> Reading:
    try:
        return _metar(place)
    except SourceUnavailable:
        return _metar_any_distance(place)


def _open_meteo(place: Place) -> Reading:
    with _source_errors():
        row = get_open_meteo_weather(place.latitude, place.longitude).iloc[0]
    return Reading(
        source="open-meteo",
        kind="model",
        site=place.label,
        distance_km=None,
        observed_at=row["datetime"].to_pydatetime(),
        **_row_values(row),
    )


SOURCES: Dict[str, Callable[[Place], Reading]] = {
    "weatherunion": _weatherunion,
    "openweathermap": _openweathermap,
    "metar": _metar,
    "open-meteo": _open_meteo,
}
# explicit metar accepts any distance; auto leaves far airports to later sources
_EXPLICIT_SOURCES = {**SOURCES, "metar": _metar_nearest}


def _choose_place(results: Sequence[Dict[str, Any]], name: str) -> Dict[str, Any]:
    """Prefer an exact name: the geocoder matches prefixes ("Leh" -> Le Havre)."""
    exact = [hit for hit in results if hit["name"].lower() == name.strip().lower()]
    return (exact or list(results))[0]


def locate(place: Optional[str], lat: Optional[float], lon: Optional[float]) -> Place:
    """Resolve coordinates, a place name, or (with neither) the IP address."""
    if lat is not None and lon is not None:
        return Place(lat, lon, f"{lat:.3f}, {lon:.3f}")
    if place:
        found = _get_json(
            "https://geocoding-api.open-meteo.com/v1/search",
            {"name": place, "count": 10},
        ).get("results")
        if not found:
            raise SourceUnavailable(f"Cannot find a place called '{place}'")
        hit = _choose_place(found, place)
        return Place(
            hit["latitude"],
            hit["longitude"],
            ", ".join(x for x in (hit["name"], hit.get("country")) if x),
        )
    data = _get_json("https://ipinfo.io/json", {})
    if "loc" not in data:
        raise SourceUnavailable("IP location is unavailable; pass a place name")
    latitude, longitude = (float(x) for x in data["loc"].split(","))
    label = ", ".join(x for x in (data.get("city"), data.get("country")) if x)
    return Place(latitude, longitude, f"{label} (approximate, from IP)")


def get_live_weather(
    place: Place, source: str = "auto"
) -> Tuple[Optional[Reading], Dict[str, str]]:
    """Return the first reading available, and why earlier sources were passed."""
    candidates = SOURCES if source == "auto" else {source: _EXPLICIT_SOURCES[source]}
    skipped: Dict[str, str] = {}
    for name, fetch in candidates.items():
        try:
            return fetch(place), skipped
        except SourceUnavailable as err:
            skipped[name] = str(err)
    return None, skipped


def heat_index_value(reading: Reading) -> Optional[float]:
    """Heat Index of a reading, or None where the formula does not apply."""
    if reading.temperature is None or reading.humidity is None:
        return None
    if reading.temperature < _HEAT_INDEX_MIN_C:
        return None
    return float(cast(float, heat_index(reading.temperature, reading.humidity)))


def get_location(
    place: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> pd.DataFrame:
    """Find a place by name, or find the caller from their IP address.

    With no arguments the IP address is sent to ipinfo.io, and the result is
    approximate. A place name is sent to the Open-Meteo geocoder.

    Args:
        place: place name.
        latitude: latitude, used with ``longitude``.
        longitude: longitude, used with ``latitude``.

    Returns:
        DataFrame with one row: ``latitude``, ``longitude`` and ``label``.

    Raises:
        SourceUnavailable: if the place cannot be found.
    """
    return pd.DataFrame([asdict(locate(place, latitude, longitude))])


def get_current_weather(
    place: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    source: str = "auto",
) -> pd.DataFrame:
    """Return live weather for a place, or for the caller's IP location.

    Sources are tried from the most local to the least: ``weatherunion``
    (needs ``WEATHERUNION_API_KEY``), ``openweathermap`` (needs
    ``OPENWEATHERMAP_API_KEY``), ``metar`` (nearest airport within 50 km) and
    ``open-meteo``. Naming ``source="metar"`` allows an airport at any distance.

    Args:
        place: place name. Default: your location, from your IP address.
        latitude: latitude, used with ``longitude``.
        longitude: longitude, used with ``latitude``.
        source: ``"auto"`` or one source name.

    Returns:
        DataFrame with one row: ``place``, ``latitude``, ``longitude``,
        ``source``, ``kind`` (``"station"``, ``"airport"`` or ``"model"``),
        ``site``, ``distance_km``, ``temperature`` (°C), ``humidity`` (%),
        ``heat_index`` (°C), ``wind_speed`` (m/s), ``wind_direction`` (degrees)
        and ``observed_at`` (UTC). ``attrs["skipped"]`` says why earlier
        sources were passed.

    Raises:
        ValueError: if ``source`` is unknown.
        SourceUnavailable: if the place cannot be found or no source answers.
    """
    if source != "auto" and source not in SOURCES:
        raise ValueError(f"Unknown source '{source}'")
    where = locate(place, latitude, longitude)
    reading, skipped = get_live_weather(where, source)
    if reading is None:
        reasons = "; ".join(f"{name}: {why}" for name, why in skipped.items())
        raise SourceUnavailable(f"No source could answer: {reasons}")
    frame = pd.DataFrame(
        [
            {
                "place": where.label,
                "latitude": where.latitude,
                "longitude": where.longitude,
                **asdict(reading),
            }
        ]
    )
    frame.insert(
        cast(int, frame.columns.get_loc("wind_speed")),
        "heat_index",
        heat_index_value(reading),
    )
    frame.attrs["skipped"] = skipped
    return frame
