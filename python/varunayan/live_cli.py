"""The varunayan live and historical commands."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Dict, Optional, Sequence, Tuple

import pandas as pd
import requests
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from .core import era5ify_point
from .live_sources import get_open_meteo_weather
from .live_weather import (
    Place,
    Reading,
    SourceUnavailable,
    get_live_weather,
    heat_index_value,
    locate,
)

_HISTORICAL_ROWS_SHOWN = 24
_Bands = Sequence[Tuple[float, str]]  # (upper bound, style), ascending
_ABOVE_ALL = float("inf")
_TEMPERATURE_BANDS: _Bands = (
    (10, "blue"),
    (20, "cyan"),
    (28, "green"),
    (34, "dark_orange"),
    (_ABOVE_ALL, "red"),
)
_HUMIDITY_BANDS: _Bands = (
    (30, "yellow"),
    (60, "green"),
    (80, "cyan"),
    (_ABOVE_ALL, "blue"),
)
# m/s; Beaufort 6 and 8
_WIND_BANDS: _Bands = ((10.8, "green"), (17.2, "yellow"), (_ABOVE_ALL, "red"))


def _styled(value: Optional[float], unit: str, bands: _Bands) -> str:
    if value is None:
        return "[dim]n/a[/dim]"
    style = next(style for limit, style in bands if value < limit)
    return f"[{style}]{value:.1f} {unit}[/{style}]"


def _rain_text(reading: Reading) -> str:
    if reading.rainfall is not None:
        style = "blue" if reading.rainfall > 0 else "dim"
        return f"[{style}]{reading.rainfall:.1f} mm/h[/{style}]"
    if reading.rain_reported is None:
        return "[dim]n/a[/dim]"
    if reading.rain_reported:
        return "[blue]Raining (amount not reported)[/blue]"
    return "[dim]None reported[/dim]"


def _age_text(reading: Reading) -> str:
    if reading.observed_at is None:
        return "live (the source gives no time)"
    minutes = int(
        (datetime.now(timezone.utc) - reading.observed_at).total_seconds() / 60
    )
    return f"{max(minutes, 0)} min ago"


def _kind_text(reading: Reading) -> str:
    return {
        "station": "Ground station",
        "airport": "Airport observation (METAR)",
        "model": "Model estimate, not a measurement",
    }[reading.kind]


def _render(
    console: Console, place: Place, reading: Reading, skipped: Dict[str, str]
) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()
    temperature = _styled(reading.temperature, "°C", _TEMPERATURE_BANDS)
    table.add_row("Temperature", f"[bold]{temperature}[/bold]")
    feels = heat_index_value(reading)
    if feels is not None:
        table.add_row("Heat index", _styled(feels, "°C", _TEMPERATURE_BANDS))
    table.add_row("Humidity", _styled(reading.humidity, "%", _HUMIDITY_BANDS))
    table.add_row("Rainfall", _rain_text(reading))
    wind = f"💨 {_styled(reading.wind_speed, 'm/s', _WIND_BANDS)}"
    if reading.wind_direction is not None:
        wind += f" from {reading.wind_direction:.0f}°"
    table.add_row("Wind", wind)
    table.add_row("", "")
    table.add_row("Type", _kind_text(reading))
    site = reading.site
    if reading.distance_km is not None:
        site += f" ({reading.distance_km:.1f} km away)"
    table.add_row("From", escape(site))
    table.add_row("Observed", _age_text(reading))
    table.add_row("Source", reading.source)
    console.print(Panel(table, title=escape(place.label), expand=False))
    for name, why in skipped.items():
        console.print(
            f"Skipped {name}: {why}", style="dim", markup=False, highlight=False
        )


def _report_error(args: argparse.Namespace, message: str) -> int:
    if args.json:
        print(json.dumps({"error": message}))
    else:
        Console(stderr=True).print(message, style="red", markup=False, highlight=False)
    return 1


def _fetch_history(
    args: argparse.Namespace, place: Place, frequency: str
) -> pd.DataFrame:
    if args.source == "open-meteo":
        return get_open_meteo_weather(
            place.latitude, place.longitude, args.start, args.end
        ).melt(
            id_vars=["datetime", "latitude", "longitude"],
            var_name="variable",
            value_name="value",
        )
    return era5ify_point(
        request_id=f"historical_{place.latitude:.2f}_{place.longitude:.2f}",
        variables=[v.strip() for v in args.variables.split(",")],
        start_date=args.start,
        end_date=args.end,
        lat=place.latitude,
        lon=place.longitude,
        frequency=frequency,
    )


def run_historical(args: argparse.Namespace) -> int:
    """Run varunayan historical; returns the exit code."""
    status = Console(stderr=True)
    use_open_meteo = args.source == "open-meteo"
    if use_open_meteo and args.freq not in (None, "hourly"):
        return _report_error(args, "Open-Meteo history is hourly: use --freq hourly")
    frequency = "hourly" if use_open_meteo else args.freq or "daily"
    try:
        with status.status("Finding your location..."):
            place = locate(args.place, args.lat, args.lon)
        with status.status(f"Getting {args.source} data for {escape(place.label)}..."):
            data = _fetch_history(args, place, frequency)
    except (RuntimeError, ValueError, OSError, requests.RequestException) as err:
        return _report_error(args, str(err))

    if args.path:
        data.to_csv(args.path, index=False)
    if args.json:
        records = json.loads(data.to_json(orient="records", date_format="iso"))
        print(json.dumps({"place": asdict(place), "rows": records}))
        return 0

    wide = data.pivot_table(index="datetime", columns="variable", values="value")
    wide = wide.sort_index().tail(_HISTORICAL_ROWS_SHOWN)
    table = Table(title=f"{escape(place.label)}: {args.source} {frequency}")
    table.add_column("Time")
    for variable in wide.columns:
        table.add_column(str(variable), justify="right")
    for moment, row in wide.iterrows():
        cells = ["n/a" if pd.isna(v) else f"{v:.2f}" for v in row]
        table.add_row(str(moment), *cells)

    console = Console()
    console.print(table)
    note = f"{len(data):,} rows"
    if data["datetime"].nunique() > _HISTORICAL_ROWS_SHOWN:
        note += f"; showing the last {_HISTORICAL_ROWS_SHOWN} time steps"
    if args.path:
        note += f"; saved to {args.path}"
    console.print(f"[dim]{note}[/dim]", highlight=False)
    return 0


def run_live(args: argparse.Namespace) -> int:
    """Run varunayan live; returns the exit code."""
    console = Console()
    status = Console(stderr=True)
    try:
        with status.status("Finding your location..."):
            place = locate(args.place, args.lat, args.lon)
        with status.status("Getting live weather..."):
            reading, skipped = get_live_weather(place, args.source)
    except SourceUnavailable as err:
        return _report_error(args, str(err))

    if args.json:
        payload = {
            "place": asdict(place),
            "reading": asdict(reading) if reading else None,
            "heat_index": heat_index_value(reading) if reading else None,
            "skipped": skipped,
        }
        print(json.dumps(payload, default=str))
    elif reading:
        _render(console, place, reading, skipped)
    else:
        status.print("[red]No source could answer for this place.[/red]")
        for name, why in skipped.items():
            status.print(f"  {name}: {why}", markup=False, highlight=False)
    return 0 if reading else 1
