"""Write cases.json with expected values from plain-loop oracles."""

import json
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

HERE = Path(__file__).parent
rng = random.Random(20261018)
cases: List[Dict[str, Any]] = []


def nan_to_none(v: Any) -> Any:
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def add(
    name: str,
    function: str,
    args: Dict[str, Any],
    expected: Any,
    data: Optional[Dict[str, list]] = None,
    tol: float = 1e-9,
) -> None:
    case: Dict[str, Any] = {
        "name": name,
        "function": function,
        "args": args,
        "tol": tol,
    }
    if data is not None:
        case["data"] = {k: [nan_to_none(x) for x in v] for k, v in data.items()}
    if isinstance(expected, dict):
        expected = {k: [nan_to_none(x) for x in v] for k, v in expected.items()}
    else:
        expected = [nan_to_none(x) for x in expected]
    case["expected"] = expected
    cases.append(case)


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def rows(data: Dict[str, list]) -> List[Dict[str, Any]]:
    keys = list(data)
    return [dict(zip(keys, vals)) for vals in zip(*data.values())]


def group(
    rs: List[Dict[str, Any]], keys: Sequence[str]
) -> Dict[tuple, List[Dict[str, Any]]]:
    out: Dict[tuple, List[Dict[str, Any]]] = {}
    for r in rs:
        out.setdefault(tuple(r[k] for k in keys), []).append(r)
    return dict(sorted(out.items()))


def grid_data(
    n_lat: int,
    n_lon: int,
    years: Sequence[int],
    months: Sequence[int],
    lat0: float = 10.0,
    res: float = 0.25,
    nan_frac: float = 0.0,
) -> Dict[str, list]:
    d: Dict[str, list] = {
        "latitude": [],
        "longitude": [],
        "year": [],
        "month": [],
        "value": [],
    }
    for i in range(n_lat):
        for j in range(n_lon):
            for y in years:
                for m in months:
                    v = round(20 + 5 * math.sin(m / 2) + i - j + rng.uniform(-3, 3), 4)
                    if rng.random() < nan_frac:
                        v = float("nan")
                    d["latitude"].append(lat0 + i * res)
                    d["longitude"].append(70.0 + j * res)
                    d["year"].append(y)
                    d["month"].append(m)
                    d["value"].append(v)
    return d


for k, (nl, nn, yrs, mos, w, by, nanf) in enumerate(
    [
        (3, 4, [2000, 2001], [1, 2, 3], "coslat", ["year", "month"], 0.0),
        (5, 2, [2010], list(range(1, 13)), "coslat", ["year", "month"], 0.1),
        (4, 4, [1990, 1991, 1992], [6, 7], None, ["year", "month"], 0.0),
        (2, 6, [2000, 2001, 2002, 2003], [1], "coslat", ["year"], 0.0),
        (6, 3, [2020], [3, 4], None, [], 0.2),
        (3, 3, [2001, 2002], [1, 12], "coslat", ["month"], 0.05),
    ]
):
    lat0 = [10.0, -30.0, 50.0, 0.0, 65.0, 25.0][k]
    d = grid_data(nl, nn, yrs, mos, lat0=lat0, nan_frac=nanf)
    rs = [r for r in rows(d) if not math.isnan(r["value"])]
    exp: Dict[str, list] = {c: [] for c in by + ["value"]}
    for key, g in group(rs, by).items() if by else [((), rs)]:
        ws = [math.cos(math.radians(r["latitude"])) if w else 1.0 for r in g]
        for c, v in zip(by, key):
            exp[c].append(v)
        exp["value"].append(sum(wi * r["value"] for wi, r in zip(ws, g)) / sum(ws))
    if "year" in by and "month" in by:
        exp["date"] = [f"{y:04d}-{m:02d}-01" for y, m in zip(exp["year"], exp["month"])]
    add(
        f"spatial_mean_{k}",
        "spatial_mean",
        {"value": "value", "by": by, "weight": w},
        exp,
        d,
    )


def compare_oracle(rs: List[Dict[str, Any]], x: str, y: str) -> List[float]:
    rs = [
        r
        for r in rs
        if r[x] is not None
        and r[y] is not None
        and not math.isnan(r[x])
        and not math.isnan(r[y])
    ]
    xs, ys = [r[x] for r in rs], [r[y] for r in rs]
    n = len(xs)
    d = [b - a for a, b in zip(xs, ys)]
    if n > 1:
        mx, my = mean(xs), mean(ys)
        sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
        sxx = sum((a - mx) ** 2 for a in xs)
        syy = sum((b - my) ** 2 for b in ys)
        r = sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else float("nan")
    else:
        r = float("nan")
    return [n, r, mean(d), math.sqrt(mean([v * v for v in d]))]


for k, (n, n_groups, noise, nanf) in enumerate(
    [
        (30, 0, 1.0, 0.0),
        (50, 3, 0.5, 0.0),
        (40, 4, 2.0, 0.1),
        (12, 2, 0.1, 0.0),
        (100, 5, 5.0, 0.05),
        (8, 0, 0.0, 0.0),
        (60, 6, 1.0, 0.2),
        (25, 1, 3.0, 0.0),
    ]
):
    d: Dict[str, list] = {"region": [], "x": [], "y": []}
    for i in range(n):
        xv = rng.uniform(0, 100)
        yv = 0.9 * xv + 3 + rng.gauss(0, noise)
        if rng.random() < nanf:
            yv = float("nan")
        d["region"].append(f"r{i % n_groups}" if n_groups else "all")
        d["x"].append(round(xv, 4))
        d["y"].append(round(yv, 4))
    by = ["region"] if n_groups else []
    exp = {c: [] for c in by + ["n", "r", "bias", "rmse"]}
    for key, g in group(rows(d), by).items() if by else [((), rows(d))]:
        for c, v in zip(by, key):
            exp[c].append(v)
        for c, v in zip(["n", "r", "bias", "rmse"], compare_oracle(g, "x", "y")):
            exp[c].append(v)
    if not by:
        d.pop("region")
    add(f"compare_{k}", "compare", {"x": "x", "y": "y", "by": by or None}, exp, d)

# Perfect agreement and a constant series (r undefined).
add(
    "compare_identical",
    "compare",
    {"x": "x", "y": "y", "by": None},
    {"n": [4], "r": [1.0], "bias": [0.0], "rmse": [0.0]},
    {"x": [1.0, 2.0, 3.0, 4.0], "y": [1.0, 2.0, 3.0, 4.0]},
)
add(
    "compare_constant_y",
    "compare",
    {"x": "x", "y": "y", "by": None},
    {"n": [3], "r": [float("nan")], "bias": [3.0], "rmse": [math.sqrt(29 / 3)]},
    {"x": [1.0, 2.0, 3.0], "y": [5.0, 5.0, 5.0]},
)

for k, (n, baseline) in enumerate(
    [(10, None), (30, [1991, 2000]), (5, [1983, 1983]), (20, [1985, 1999])]
):
    years = list(range(1981, 1981 + n))
    vals = [round(25 + 0.02 * (y - 1981) + rng.uniform(-1, 1), 4) for y in years]
    ref = [
        v
        for y, v in zip(years, vals)
        if baseline is None or baseline[0] <= y <= baseline[1]
    ]
    add(
        f"anomaly_{k}",
        "anomaly",
        {"value": "t", "baseline": baseline},
        [v - mean(ref) for v in vals],
        {"year": years, "t": vals},
    )

for k, by in enumerate([[], ["site"], ["site"], []]):
    d = {"site": [], "year": [], "month": [], "v": []}
    for s in ["a", "b", "c"] if by else ["a"]:
        for y in range(2000, 2000 + rng.randint(2, 5)):
            for m in rng.sample(range(1, 13), 12):
                d["site"].append(s)
                d["year"].append(y)
                d["month"].append(m)
                d["v"].append(round(rng.uniform(-10, 40), 4))
    keys = by + ["month"]
    exp = {c: [] for c in keys + ["v"]}
    for key, g in group(rows(d), keys).items():
        for c, v in zip(keys, key):
            exp[c].append(v)
        exp["v"].append(mean([r["v"] for r in g]))
    add(
        f"seasonal_cycle_{k}",
        "seasonal_cycle",
        {"value": "v", "by": by or None},
        exp,
        d,
    )


def peak_oracle(d: Dict[str, list], value: str, by: List[str]) -> Dict[str, list]:
    exp = {c: [] for c in by + ["peak_month", "peak_value", "annual_total"]}
    for key, g in group(rows(d), by).items():
        clim = {
            m: mean([r[value] for r in rs]) for (m,), rs in group(g, ["month"]).items()
        }
        best = max(sorted(clim), key=lambda m: (clim[m], -m))  # first month wins a tie
        for c, v in zip(by, key):
            exp[c].append(v)
        exp["peak_month"].append(best)
        exp["peak_value"].append(clim[best])
        exp["annual_total"].append(sum(clim.values()))
    return exp


for k, (nl, nn, yrs) in enumerate(
    [
        (2, 2, [2000, 2001]),
        (3, 5, [2010, 2011, 2012]),
        (1, 1, [1999]),
        (4, 3, list(range(1990, 2000))),
    ]
):
    d = grid_data(nl, nn, yrs, list(range(1, 13)))
    add(
        f"peak_month_{k}",
        "peak_month",
        {"value": "value"},
        peak_oracle(d, "value", ["latitude", "longitude"]),
        d,
    )

tie = {
    "latitude": [10.0] * 12,
    "longitude": [70.0] * 12,
    "month": list(range(1, 13)),
    "value": [1.0, 5.0, 2.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
}
add(
    "peak_month_tie_first_wins",
    "peak_month",
    {"value": "value"},
    {
        "latitude": [10.0],
        "longitude": [70.0],
        "peak_month": [2],
        "peak_value": [5.0],
        "annual_total": [13.0],
    },
    tie,
)
add(
    "peak_month_by_region",
    "peak_month",
    {"value": "v", "by": ["region"]},
    peak_oracle(
        {
            "region": ["n"] * 12 + ["s"] * 12,
            "month": list(range(1, 13)) * 2,
            "v": [float(m) for m in range(1, 13)]
            + [float(13 - m) for m in range(1, 13)],
        },
        "v",
        ["region"],
    ),
    {
        "region": ["n"] * 12 + ["s"] * 12,
        "month": list(range(1, 13)) * 2,
        "v": [float(m) for m in range(1, 13)] + [float(13 - m) for m in range(1, 13)],
    },
)

for k, (months, how) in enumerate(
    [
        ([6, 7, 8], "sum"),
        ([6, 7, 8], "mean"),
        ([12, 1, 2], "sum"),
        ([5], "mean"),
        (list(range(1, 13)), "sum"),
    ]
):
    d = grid_data(2, 3, [2001, 2002, 2003], list(range(1, 13)))
    keys = ["latitude", "longitude"]
    exp = {c: [] for c in keys + ["value"]}
    for key, g in group(rows(d), keys).items():
        per_year = []
        for _, gy in group([r for r in g if r["month"] in months], ["year"]).items():
            vs = [r["value"] for r in gy]
            per_year.append(sum(vs) if how == "sum" else mean(vs))
        for c, v in zip(keys, key):
            exp[c].append(v)
        exp["value"].append(mean(per_year))
    add(
        f"seasonal_stat_{k}",
        "seasonal_stat",
        {"value": "value", "months": months, "how": how},
        exp,
        d,
    )

for k, (src_res, dst_res, nl, nn, lat0) in enumerate(
    [
        (0.25, 0.5, 4, 4, 10.0),
        (0.1, 0.5, 10, 7, 20.0),
        (0.25, 1.0, 8, 8, -5.0),
        (0.5, 0.5, 3, 3, 30.25),
    ]
):
    d: Dict[str, list] = {"latitude": [], "longitude": [], "value": []}
    for i in range(nl):
        for j in range(nn):
            d["latitude"].append(round(lat0 + i * src_res, 6))
            d["longitude"].append(round(70.0 + j * src_res, 6))
            d["value"].append(round(rng.uniform(0, 30), 4))
    cell = lambda v: round(math.floor(v / dst_res + 1e-9) * dst_res + dst_res / 2, 6)  # noqa: E731
    acc: Dict[tuple, List[float]] = {}
    for r in rows(d):
        acc.setdefault((cell(r["latitude"]), cell(r["longitude"])), []).append(
            r["value"]
        )
    keys_sorted = sorted(acc)
    add(
        f"regrid_{k}",
        "regrid",
        {"value": "value", "resolution": dst_res},
        {
            "latitude": [a for a, _ in keys_sorted],
            "longitude": [b for _, b in keys_sorted],
            "value": [mean(acc[kk]) for kk in keys_sorted],
        },
        d,
    )

temps = [-20.0, -5.0, 0.0, 10.0, 25.0, 35.0, 45.0]
for k, rh in enumerate([5.0, 30.0, 60.0, 90.0, 100.0]):
    a, b = 17.625, 243.04
    dew = []
    for t in temps:
        g = math.log(rh / 100) + a * t / (b + t)
        dew.append(b * g / (a - g))
    add(
        f"dewpoint_rh{int(rh)}",
        "dewpoint_from_relative_humidity",
        {"temp_c": temps, "rh": [rh] * len(temps)},
        dew,
    )

oracle = json.loads((HERE / "ccf_oracle.json").read_text())
for o in oracle:
    add(
        o["name"],
        "cross_correlation",
        {"x": o["x"], "y": o["y"], "max_lag": o["max_lag"]},
        {
            "lag": o["lag"] if isinstance(o["lag"], list) else [o["lag"]],
            "r": o["r"] if isinstance(o["r"], list) else [o["r"]],
        },
        tol=1e-12,
    )

# era5ify output: per-cell aggregation in time, monthly totals, units.
import calendar  # noqa: E402
import datetime as _dt  # noqa: E402

METHOD = {
    "t2m": "mean",
    "tp": "sum",
    "mx2t": "max",
    "mn2t": "min",
    "u10": "mean",
    "t": "mean",
}
TEMP = {"t2m", "mx2t", "mn2t", "t"}


def era5_oracle(
    rows_in: List[Dict[str, Any]], frequency: str, convert: bool
) -> Dict[str, list]:
    has_level = "pressure_level" in rows_in[0]
    keys = ["latitude", "longitude"] + (["pressure_level"] if has_level else [])
    groups: Dict[tuple, List[float]] = {}
    for r in rows_in:
        t = _dt.datetime.fromisoformat(r["datetime"])
        v = r["value"]
        if (
            frequency in ("monthly", "yearly")
            and METHOD[r["variable"]] == "sum"
            and v is not None
        ):
            v = v * calendar.monthrange(t.year, t.month)[1]
        if frequency == "daily":
            t = _dt.datetime(t.year, t.month, t.day)
        elif frequency == "weekly":
            d = _dt.date(t.year, t.month, t.day) - _dt.timedelta(days=t.weekday())
            t = _dt.datetime(d.year, d.month, d.day)
        elif frequency == "monthly":
            t = _dt.datetime(t.year, t.month, 1)
        elif frequency == "yearly":
            t = _dt.datetime(t.year, 1, 1)
        k = (t,) + tuple(r[c] for c in keys) + (r["variable"],)
        groups.setdefault(k, []).append(v)
    out: Dict[str, list] = {c: [] for c in ["datetime"] + keys + ["variable", "value"]}
    if frequency in ("monthly", "yearly"):
        out["year"] = []
    if frequency == "monthly":
        out["month"] = []
    for k in sorted(groups):
        vals = [v for v in groups[k] if v is not None]
        var = k[-1]
        how = METHOD[var] if frequency != "hourly" else "mean"
        if not vals:
            val = float("nan")
        elif how == "sum":
            val = sum(vals)
        elif how == "max":
            val = max(vals)
        elif how == "min":
            val = min(vals)
        else:
            val = mean(vals)
        if convert and var in TEMP:
            val -= 273.15
        if convert and var == "tp":
            val *= 1000
        out["datetime"].append(k[0].strftime("%Y-%m-%d %H:%M:%S"))
        for c, v in zip(keys, k[1:-1]):
            out[c].append(v)
        out["variable"].append(var)
        out["value"].append(val)
        if "year" in out:
            out["year"].append(k[0].year)
        if "month" in out:
            out["month"].append(k[0].month)
    return out


def era5_input(
    times: List[_dt.datetime],
    variables: List[str],
    cells: List[tuple],
    levels: Optional[List[int]] = None,
    nan_frac: float = 0.0,
) -> List[Dict[str, Any]]:
    base = {
        "t2m": 290.0,
        "tp": 0.004,
        "mx2t": 300.0,
        "mn2t": 280.0,
        "u10": 2.0,
        "t": 270.0,
    }
    rows_in = []
    for t in times:
        for lat, lon in cells:
            for lev in levels or [None]:
                for var in variables:
                    v: Optional[float] = round(base[var] * rng.uniform(0.8, 1.2), 6)
                    if rng.random() < nan_frac:
                        v = None
                    r = {
                        "datetime": t.strftime("%Y-%m-%d %H:%M:%S"),
                        "latitude": lat,
                        "longitude": lon,
                        "variable": var,
                        "value": v,
                    }
                    if lev is not None:
                        r["pressure_level"] = lev
                    rows_in.append(r)
    return rows_in


def add_era5(
    name: str, rows_in: List[Dict[str, Any]], frequency: str, convert: bool = True
) -> None:
    data = {c: [r[c] for r in rows_in] for c in rows_in[0]}
    add(
        name,
        "era5_grid_output",
        {"frequency": frequency, "convert_units": convert},
        era5_oracle(rows_in, frequency, convert),
        data,
    )


cells2 = [(20.0, 72.0), (20.25, 72.0)]
allv = ["t2m", "tp", "mx2t", "mn2t", "u10"]
hours = lambda start, n, step=1: [
    start + _dt.timedelta(hours=step * i) for i in range(n)
]  # noqa: E731
add_era5(
    "era5_hourly",
    era5_input(hours(_dt.datetime(2024, 5, 1), 6), allv, cells2),
    "hourly",
)
add_era5(
    "era5_hourly_no_units",
    era5_input(hours(_dt.datetime(2024, 5, 1), 4), allv, cells2),
    "hourly",
    False,
)
add_era5(
    "era5_daily",
    era5_input(hours(_dt.datetime(2024, 5, 1), 12, 6), allv, cells2),
    "daily",
)
add_era5(
    "era5_daily_missing",
    era5_input(hours(_dt.datetime(2024, 5, 1), 8, 6), allv, cells2, nan_frac=0.4),
    "daily",
)
add_era5(
    "era5_daily_all_missing",
    [
        dict(r, value=None) if r["variable"] == "tp" and r["latitude"] == 20.0 else r
        for r in era5_input(
            hours(_dt.datetime(2024, 5, 1), 4, 6), ["tp", "t2m"], cells2
        )
    ],
    "daily",
)
add_era5(
    "era5_weekly",
    era5_input(hours(_dt.datetime(2025, 12, 27), 18, 24), allv, cells2[:1]),
    "weekly",
)
months = lambda y0, m0, n: [
    _dt.datetime(y0 + (m0 - 1 + i) // 12, (m0 - 1 + i) % 12 + 1, 1) for i in range(n)
]  # noqa: E731
add_era5(
    "era5_monthly_leap_feb",
    era5_input(months(2024, 1, 3), ["t2m", "tp"], cells2),
    "monthly",
)
add_era5(
    "era5_monthly_no_units",
    era5_input(months(2023, 11, 4), ["t2m", "tp"], cells2),
    "monthly",
    False,
)
add_era5(
    "era5_yearly", era5_input(months(2023, 1, 24), ["t2m", "tp"], cells2), "yearly"
)
add_era5(
    "era5_pressure_daily",
    era5_input(
        hours(_dt.datetime(2024, 7, 1), 8, 6), ["t"], cells2, levels=[500, 850, 1000]
    ),
    "daily",
)

# Heat stress: the R package (checked against published references) is the
# oracle; see make_heat_oracle.R.
for o in json.loads((HERE / "heat_oracle.json").read_text()):
    add(o["name"], o["function"], o["args"], o["expected"], tol=o["tol"])

(HERE / "cases.json").write_text(json.dumps(cases, indent=1) + "\n")
print(f"wrote {len(cases)} cases")

# Plot cases: both packages must draw the same number of panels with the
# same title and vertical axis label.
plots: List[Dict[str, Any]] = []


def add_plot(
    name: str,
    function: str,
    data: Dict[str, list],
    args: Dict[str, Any],
    n_panels: int,
    title: Optional[str],
    ylabel: Optional[str] = None,
) -> None:
    plots.append(
        {
            "name": name,
            "function": function,
            "data": data,
            "args": args,
            "expected": {"n_panels": n_panels, "title": title, "ylabel": ylabel},
        }
    )


g = grid_data(4, 5, [2001], [1])
g["t_min"] = [v - 5 for v in g["value"]]
g["period"] = ["a", "b"] * (len(g["value"]) // 2)
add_plot(
    "map_one_column", "plot_map", g, {"column": "value", "title": "Grid"}, 1, "Grid"
)
add_plot("map_two_columns", "plot_map", g, {"column": ["value", "t_min"]}, 2, None)
add_plot(
    "map_facet",
    "plot_map",
    g,
    {"column": "value", "facet": "period", "title": "By period"},
    2,
    "By period",
)
add_plot("map_log", "plot_map", g, {"column": "value", "log": True}, 1, None)
g_bias = dict(g)
g_bias["bias"] = [v - 22 for v in g["value"]]
add_plot(
    "map_center",
    "plot_map",
    g_bias,
    {"column": "bias", "cmap": "RdBu", "center": 0, "title": "Bias"},
    1,
    "Bias",
)
pm = dict(g)
pm["peak_month"] = [1 + i % 12 for i in range(len(g["value"]))]
add_plot(
    "map_months", "plot_map", pm, {"column": "peak_month", "months": True}, 1, None
)

s = {"year": [], "region": [], "country": [], "t": [], "lo": [], "hi": []}
for c, r in [("A", "north"), ("B", "north"), ("C", "south")]:
    for y in range(2001, 2021):
        v = round(20 + 0.05 * (y - 2001) + rng.uniform(-1, 1), 4)
        for k2, v2 in zip(
            ["year", "region", "country", "t", "lo", "hi"], [y, r, c, v, v - 2, v + 2]
        ):
            s[k2].append(v2)
add_plot(
    "series_by_lowess",
    "plot_series",
    s,
    {
        "x": "year",
        "y": "t",
        "by": "country",
        "smooth": "lowess",
        "ylabel": "Temperature",
    },
    1,
    None,
    "Temperature",
)
add_plot(
    "series_facet",
    "plot_series",
    s,
    {"x": "year", "y": "t", "by": "country", "facet": "region", "title": "Trend"},
    2,
    "Trend",
    "t",
)
one = {k2: v2[:20] for k2, v2 in s.items()}
add_plot(
    "series_linear",
    "plot_series",
    one,
    {"x": "year", "y": "t", "smooth": "linear"},
    1,
    None,
    "t",
)
mo = {
    "month": list(range(1, 13)),
    "t": [float(10 + m) for m in range(1, 13)],
    "lo": [float(5 + m) for m in range(1, 13)],
    "hi": [float(15 + m) for m in range(1, 13)],
}
add_plot(
    "series_month_ribbon",
    "plot_series",
    mo,
    {"x": "month", "y": "t", "ribbon": ["lo", "hi"]},
    1,
    None,
    "t",
)

dual = {
    "m": list(range(1, 25)),
    "rain": [abs(math.sin(i / 2)) * 300 for i in range(24)],
    "searches": [abs(math.sin(i / 2)) * 80 + 1 for i in range(24)],
}
add_plot(
    "dual_axis",
    "plot_dual_axis",
    dual,
    {"x": "m", "left": "rain", "right": "searches", "log_right": True, "title": "Rain"},
    1,
    "Rain",
    "rain",
)
cc = {"lag": list(range(-3, 4)), "r": [0.1, 0.3, 0.8, 0.5, 0.2, 0.0, -0.1]}
add_plot("ccf", "plot_ccf", cc, {}, 1, None, "Cross-correlation")
sc = {
    "cru": [float(i) for i in range(20)],
    "era5": [i + rng.uniform(-1, 1) for i in range(20)],
}
add_plot(
    "scatter",
    "plot_scatter",
    sc,
    {"x": "cru", "y": "era5", "title": "ERA5 vs CRU"},
    1,
    "ERA5 vs CRU",
    "era5",
)
bars = {
    "state": [f"s{i}" for i in range(10)],
    "r": [rng.uniform(0.5, 1) for _ in range(10)],
}
add_plot("bars_vertical", "plot_bars", bars, {"x": "state", "y": "r"}, 1, None, "r")
dev = {"year": list(range(2001, 2011)), "dev": [i / 5 - 1 for i in range(10)]}
add_plot(
    "bars_diverging",
    "plot_bars",
    dev,
    {"x": "year", "y": "dev", "title": "Anomaly"},
    1,
    "Anomaly",
    "dev",
)
hm = {
    "country": [c for c in ["A", "B"] for _ in range(12)],
    "month": list(range(1, 13)) * 2,
    "t": [float(m) for m in range(24)],
}
add_plot(
    "heatmap_long",
    "plot_heatmap",
    hm,
    {"x": "month", "y": "country", "value": "t", "title": "Heat"},
    1,
    "Heat",
)

(HERE / "plot_cases.json").write_text(json.dumps(plots, indent=1) + "\n")
print(f"wrote {len(plots)} plot cases")
