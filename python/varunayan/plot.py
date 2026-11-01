"""Matplotlib plots matching the R ggplot2 functions; each returns a closed Figure."""

import calendar
import functools
from typing import Any, Callable, List, Optional, Sequence, Tuple, TypeVar, Union, cast

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, Colormap, ListedColormap, LogNorm, Normalize
from matplotlib.ticker import MaxNLocator
from matplotlib.figure import Figure

from .processing.variable_lists import is_sum_var

MONTH_LABELS = [calendar.month_abbr[m] for m in range(1, 13)]
MONTH_COLORS = [
    "#e6194b",
    "#f58231",
    "#ffe119",
    "#bfef45",
    "#3cb44b",
    "#42d4f4",
    "#4363d8",
    "#0000ff",
    "#911eb4",
    "#f032e6",
    "#fabed4",
    "#a40000",
]
PALETTE = ["#B2182B", "#2166AC", "#1B7837", "#E08214", "#762A83", "#4D4D4D"]

# first installed one with a bold face wins, as in vayuayan
FONTS = ["SF Pro Text", "Helvetica Neue", "Helvetica", "Inter", "Arial", "DejaVu Sans"]

DPI = 150

_F = TypeVar("_F", bound=Callable[..., Figure])


def _fonts_with_bold() -> List[str]:
    """Installed FONTS with a bold face; macOS Helvetica loads as regular only."""
    from matplotlib import font_manager

    weights: dict = {}
    for f in font_manager.fontManager.ttflist:
        w = (
            f.weight
            if isinstance(f.weight, int)
            else font_manager.weight_dict.get(f.weight, 400)
        )
        weights.setdefault(f.name, set()).add(w)
    return [f for f in FONTS if max(weights.get(f, {0})) >= 600] or ["sans-serif"]


def _themed(plot: _F) -> _F:
    """Draw the figure with FONTS; text keeps its font after the context ends."""

    @functools.wraps(plot)
    def wrapper(*args: Any, **kwargs: Any) -> Figure:
        from matplotlib import rc_context

        with rc_context({"font.family": _fonts_with_bold()}):
            return plot(*args, **kwargs)

    return cast(_F, wrapper)


def _subplots(*args: Any, **kwargs: Any) -> Tuple[Figure, Any]:
    kwargs.setdefault("dpi", DPI)
    fig, axes = plt.subplots(*args, **kwargs)
    return fig, axes


def _finish(fig: Figure, title: Optional[str]) -> Figure:
    if title:
        fig.suptitle(title)
    fig.tight_layout()
    plt.close(fig)
    return fig


def _month_axis(ax: plt.Axes) -> None:
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTH_LABELS)


@_themed
def plot_map(
    data: pd.DataFrame,
    column: Union[str, Sequence[str]],
    boundaries: Optional[gpd.GeoDataFrame] = None,
    facet: Optional[str] = None,
    log: bool = False,
    months: bool = False,
    labels: Optional[str] = None,
    cmap: str = "viridis",
    center: Optional[float] = None,
    title: Optional[str] = None,
    legend_title: Optional[str] = None,
) -> Figure:
    """Map one or more columns of gridded or polygon data.

    A GeoDataFrame with polygons gives a choropleth. A DataFrame with
    ``latitude`` and ``longitude`` gives one square for each grid point.

    Args:
        data: Polygon GeoDataFrame, or DataFrame with latitude and longitude.
        column: Column to colour by. A list gives one panel per column, with
            one shared colour scale.
        boundaries: Optional polygons to draw as outlines on top.
        facet: Optional column; one panel per value (for example a period).
        log: Use a log colour scale (values must be positive).
        months: The values are months (1-12). Use 12 discrete colours and
            month names in the legend, for example for ``peak_month``.
        labels: Optional column to write at each polygon centre.
        cmap: Matplotlib colour map.
        center: Centre a diverging colour map on this value, with limits
            the same distance on each side (for example 0 for a bias).
        title: Figure title.
        legend_title: Colour bar or legend title. Default: the column name.

    Returns:
        Matplotlib Figure.
    """
    columns = [column] if isinstance(column, str) else list(column)
    if facet is not None:
        panels = [
            (str(v), data[data[facet] == v], columns[0]) for v in pd.unique(data[facet])
        ]
    else:
        panels = [(c if len(columns) > 1 else "", data, c) for c in columns]

    values = pd.concat([p[1][p[2]] for p in panels]).dropna()
    norm: Optional[Normalize] = None
    cmap_obj: Colormap
    if months:
        cmap_obj = ListedColormap(MONTH_COLORS)
        norm = BoundaryNorm(np.arange(0.5, 13.5), 12)
    else:
        cmap_obj = plt.get_cmap(cmap)
        if log:
            norm = LogNorm(vmin=values[values > 0].min(), vmax=values.max())
        elif center is not None:
            norm = _colour_norm(values, center)
    vmin = None if norm is not None else values.min()
    vmax = None if norm is not None else values.max()

    is_polygon = (
        isinstance(data, gpd.GeoDataFrame) and data.geom_type.iloc[0] != "Point"
    )
    fig, axes = _subplots(1, len(panels), figsize=(6 * len(panels), 6), squeeze=False)
    mappable = None
    for ax, (name, sub, col) in zip(axes[0], panels):
        if is_polygon:
            sub.plot(
                column=col,
                ax=ax,
                cmap=cmap_obj,
                norm=norm,
                vmin=vmin,
                vmax=vmax,
                edgecolor="white",
                linewidth=0.3,
                missing_kwds={"color": "lightgrey"},
            )
            mappable = ax.collections[0]
            if labels:
                for _, row in sub.dropna(subset=[col]).iterrows():
                    pt = row.geometry.representative_point()
                    ax.text(
                        pt.x, pt.y, row[labels], fontsize=6, ha="center", va="center"
                    )
        else:
            size = 4000 / max(np.sqrt(len(sub)), 1)
            mappable = ax.scatter(
                sub["longitude"],
                sub["latitude"],
                c=sub[col],
                s=size,
                marker="s",
                linewidths=0,
                cmap=cmap_obj,
                norm=norm,
                vmin=vmin,
                vmax=vmax,
            )
        if boundaries is not None:
            boundaries.boundary.plot(ax=ax, color="black", linewidth=0.4)
        ax.set_title(name)
        ax.set_aspect("equal")
        ax.set_axis_off()
    if mappable is not None:
        cbar = fig.colorbar(mappable, ax=list(axes[0]), shrink=0.7)
        cbar.set_label(legend_title or columns[0])
        if months:
            cbar.set_ticks(range(1, 13))
            cbar.set_ticklabels(MONTH_LABELS)
    if title:
        fig.suptitle(title)
    plt.close(fig)
    return fig


@_themed
def plot_series(
    data: pd.DataFrame,
    x: str,
    y: str,
    by: Optional[str] = None,
    facet: Optional[str] = None,
    smooth: Optional[str] = None,
    span: float = 2 / 3,
    ribbon: Optional[Tuple[str, str]] = None,
    title: Optional[str] = None,
    ylabel: Optional[str] = None,
) -> Figure:
    """Line plot of ``y`` against ``x``, one line per ``by`` group.

    When ``x`` is ``"month"``, the axis shows month names.

    Args:
        data: Long DataFrame.
        x: Column for the horizontal axis (for example ``date``, ``year``).
        y: Column for the vertical axis.
        by: Optional column; one line (and colour) per value.
        facet: Optional column; one panel per value.
        smooth: ``"lowess"`` or ``"linear"`` adds a trend line. The data
            line is then light grey when there is no ``by`` column.
        span: Fraction of the points in each LOWESS window (R ``f``).
        ribbon: Optional ``(low, high)`` columns to shade, for example
            ``("temperature_min", "temperature_max")``.
        title: Figure title.
        ylabel: Vertical axis label. Default: ``y``.

    Returns:
        Matplotlib Figure.
    """
    facets = list(pd.unique(data[facet])) if facet else [None]
    fig, axes = _subplots(
        len(facets), 1, figsize=(9, 3.8 * len(facets)), sharex=True, squeeze=False
    )
    # Sorted, so that a group keeps its colour from one figure to the next.
    groups = sorted(pd.unique(data[by]), key=str) if by else [None]
    colors = {
        g: (
            PALETTE[i % len(PALETTE)]
            if len(groups) <= len(PALETTE)
            else plt.get_cmap("tab20")(i % 20)
        )
        for i, g in enumerate(groups)
    }
    for ax, f in zip(axes[:, 0], facets):
        sub = data if f is None else data[data[facet] == f]
        for g in groups:
            d = (sub if g is None else sub[sub[by] == g]).sort_values(x)
            if d.empty:
                continue
            color = colors[g]
            line_color = "#BDBDBD" if smooth and g is None else color
            if ribbon:
                ax.fill_between(
                    d[x], d[ribbon[0]], d[ribbon[1]], color=color, alpha=0.15
                )
            ax.plot(
                d[x],
                d[y],
                color=line_color,
                lw=1.2,
                marker="o" if len(d) <= 40 else None,
                ms=3,
                label=None if g is None else str(g),
            )
            if smooth:
                ax.plot(
                    d[x],
                    _smooth(d[x], d[y], smooth, span),
                    color=color,
                    lw=1.8,
                    ls="--" if smooth == "linear" else "-",
                )
        if f is not None:
            ax.set_title(str(f))
        ax.set_ylabel(ylabel or y)
        ax.grid(True, alpha=0.3)
        if by:
            ax.legend(fontsize=8, ncol=2)
    last_ax: plt.Axes = axes[-1, 0]
    if x == "month":
        _month_axis(last_ax)
    elif pd.api.types.is_integer_dtype(data[x]):
        last_ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    elif pd.api.types.is_datetime64_any_dtype(data[x]):
        fig.autofmt_xdate()
    last_ax.set_xlabel("" if x in ("date", "month", "year") else x)
    return _finish(fig, title)


def _smooth(x: pd.Series, y: pd.Series, method: str, span: float) -> np.ndarray:
    xs = x.map(pd.Timestamp.toordinal) if np.issubdtype(x.dtype, np.datetime64) else x
    xs = np.asarray(xs, dtype=float)
    if method == "linear":
        fitted: np.ndarray = np.polyval(np.polyfit(xs, y, 1), xs)
        return fitted
    if method == "lowess":
        try:
            from statsmodels.nonparametric.smoothers_lowess import lowess
        except ImportError as e:
            raise ImportError(
                "smooth='lowess' needs statsmodels: pip install statsmodels"
            ) from e
        # it and delta as R stats::lowess, so the two packages draw the same line.
        delta = 0.01 * (xs.max() - xs.min())
        return lowess(  # type: ignore[no-any-return]
            y, xs, frac=span, it=3, delta=delta, return_sorted=False
        )
    raise ValueError("smooth must be 'lowess', 'linear' or None")


@_themed
def plot_dual_axis(
    data: pd.DataFrame,
    x: str,
    left: str,
    right: str,
    log_right: bool = False,
    title: Optional[str] = None,
) -> Figure:
    """Two series with different units on a left and a right axis.

    Args:
        data: DataFrame with the three columns.
        x: Column for the horizontal axis, for example ``date``.
        left: Column for the left axis.
        right: Column for the right axis.
        log_right: Show ``log(1 + right)`` on the right axis.
        title: Figure title.

    Returns:
        Matplotlib Figure.
    """
    d = data.sort_values(x)
    fig, ax1 = _subplots(figsize=(11, 4.5))
    ax1.plot(d[x], d[left], color=PALETTE[1], lw=1.2)
    ax1.set_ylabel(left, color=PALETTE[1])
    ax2 = ax1.twinx()
    rv = np.log1p(d[right]) if log_right else d[right]
    ax2.plot(d[x], rv, color=PALETTE[0], lw=1.2)
    ax2.set_ylabel(f"log(1 + {right})" if log_right else right, color=PALETTE[0])
    ax1.grid(True, alpha=0.3)
    return _finish(fig, title)


@_themed
def plot_ccf(ccf: pd.DataFrame, title: Optional[str] = None) -> Figure:
    """Stem plot of a cross-correlation from ``cross_correlation()``.

    Args:
        ccf: DataFrame with ``lag`` and ``r``.
        title: Figure title.

    Returns:
        Matplotlib Figure.
    """
    fig, ax = _subplots(figsize=(8, 4))
    ax.stem(ccf["lag"], ccf["r"], basefmt="grey")
    best = ccf.iloc[int(np.argmax(np.abs(ccf["r"].to_numpy())))]
    ax.axvline(0, color="grey", ls="--", lw=0.8)
    ax.set_xlabel("Lag")
    ax.set_ylabel("Cross-correlation")
    ax.set_title(f"Largest |r| = {best['r']:.2f} at lag {int(best['lag'])}")
    ax.grid(True, alpha=0.3)
    return _finish(fig, title)


@_themed
def plot_scatter(
    data: pd.DataFrame, x: str, y: str, title: Optional[str] = None
) -> Figure:
    """Scatter of ``y`` against ``x`` with the 1:1 line, r and bias.

    Args:
        data: DataFrame with the two columns.
        x: Column for the horizontal axis (the reference).
        y: Column for the vertical axis.
        title: Figure title.

    Returns:
        Matplotlib Figure.
    """
    d = data.dropna(subset=[x, y])
    r = d[x].corr(d[y])
    bias = (d[y] - d[x]).mean()
    lims = [min(d[x].min(), d[y].min()), max(d[x].max(), d[y].max())]
    fig, ax = _subplots(figsize=(5.5, 5.5))
    ax.plot(lims, lims, "--", color="grey", lw=0.8)
    ax.scatter(d[x], d[y], s=12, alpha=0.6, color="#34495E")
    ax.set_aspect("equal")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(f"r = {r:.3f}, bias ({y} - {x}) = {bias:+.2f}, n = {len(d)}")
    ax.grid(True, alpha=0.3)
    return _finish(fig, title)


@_themed
def plot_bars(
    data: pd.DataFrame,
    x: str,
    y: str,
    horizontal: bool = False,
    sort: bool = False,
    cmap: str = "coolwarm",
    title: Optional[str] = None,
) -> Figure:
    """Bar chart of ``y`` for each ``x``, coloured by the value of ``y``.

    Args:
        data: DataFrame with the two columns.
        x: Category column (for example ``state_name`` or ``year``).
        y: Value column.
        horizontal: Draw horizontal bars (for long category names).
        sort: Sort the bars by value, largest first.
        cmap: Colour map. A diverging map is centred on zero.
        title: Figure title.

    Returns:
        Matplotlib Figure.
    """
    d = data.dropna(subset=[y])
    if sort:
        d = d.sort_values(y, ascending=horizontal)
    lim = d[y].abs().max()
    vmin, vmax = (-lim, lim) if d[y].min() < 0 else (d[y].min(), d[y].max())
    colors = plt.get_cmap(cmap)((d[y] - vmin) / ((vmax - vmin) or 1))
    size = (8, max(4, 0.25 * len(d))) if horizontal else (max(8, 0.15 * len(d)), 4.5)
    fig, ax = _subplots(figsize=size)
    pos = np.arange(len(d))
    if horizontal:
        ax.barh(pos, d[y], color=colors)
        ax.set_yticks(pos, d[x].astype(str), fontsize=8)
        ax.set_xlabel(y)
    else:
        ax.bar(pos, d[y], color=colors)
        step = max(1, len(d) // 20)
        ax.set_xticks(pos[::step], d[x].astype(str).iloc[::step], rotation=90)
        ax.set_ylabel(y)
    ax.grid(True, axis="x" if horizontal else "y", alpha=0.3)
    return _finish(fig, title)


@_themed
def plot_heatmap(
    data: pd.DataFrame,
    x: Optional[str] = None,
    y: Optional[str] = None,
    value: Optional[str] = None,
    annotate: bool = False,
    cmap: str = "RdYlBu_r",
    title: Optional[str] = None,
) -> Figure:
    """Heat map of a matrix, or of a long DataFrame with x, y and value.

    Args:
        data: Long DataFrame (with ``x``, ``y`` and ``value``), or a wide
            matrix such as ``df.corr()`` (then leave ``x``, ``y``, ``value``).
        x: Column for the columns of the heat map (``month`` shows names).
        y: Column for the rows.
        value: Column for the colour.
        annotate: Write the value in each cell.
        cmap: Colour map.
        title: Figure title.

    Returns:
        Matplotlib Figure.
    """
    if value is None:
        mat = data
    else:
        mat = data.pivot_table(index=y, columns=x, values=value, sort=False)
    fig, ax = _subplots(
        figsize=(max(6, 0.7 * mat.shape[1]), max(4, 0.5 * mat.shape[0]))
    )
    vals = mat.to_numpy(dtype=float)
    im = ax.imshow(vals, aspect="auto", cmap=cmap)
    cols: List[str] = [
        MONTH_LABELS[int(c) - 1] if x == "month" else str(c) for c in mat.columns
    ]
    ax.set_xticks(
        range(mat.shape[1]), cols, rotation=45 if x != "month" else 0, ha="right"
    )
    ax.set_yticks(range(mat.shape[0]), [str(i) for i in mat.index])
    if annotate:
        for (i, j), v in np.ndenumerate(vals):
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, shrink=0.8, label=value or "")
    return _finish(fig, title)


MISSING = "#d9d9d9"
HOLE = 1.5  # empty centre, in rings, so the inner ring is not a point


def _radial_frame(
    data: pd.DataFrame, value: str, time: str, by: Optional[str], tz: Optional[str]
) -> pd.DataFrame:
    """Columns panel, t and value; a date-only time column is combined with hour."""
    t = pd.to_datetime(data[time], errors="coerce")
    if "hour" in data and (t.dropna() == t.dropna().dt.normalize()).all():
        t = t + pd.to_timedelta(data["hour"], unit="h")
    if tz is not None:
        if t.dt.tz is None:
            t = t.dt.tz_localize("UTC")  # ERA5 times are UTC
        t = t.dt.tz_convert(tz)
    panel = data[by].astype(str) if by else pd.Series("", index=data.index)
    d = pd.DataFrame({"panel": panel, "t": t, "value": data[value]}).dropna(
        subset=["t"]
    )
    if d.empty:
        raise ValueError(f"No dated rows in column {time!r}.")
    return d


def _colour_norm(values: pd.Series, center: Optional[float]) -> Normalize:
    """Data range, or the same distance on each side of center."""
    if center is None:
        return Normalize(vmin=values.min(), vmax=values.max())
    lim = float((values - center).abs().max())
    return Normalize(vmin=center - lim, vmax=center + lim)


def _radial_figure(panels: List[str], ncol: int) -> Tuple[Figure, List[Any]]:
    ncols = min(ncol, len(panels))
    nrows = -(-len(panels) // ncols)
    fig = plt.figure(figsize=(5 * ncols, 5 * nrows + 1), dpi=DPI, layout="constrained")
    # the suptitle overlaps polar panel titles at the default pad
    fig.get_layout_engine().set(h_pad=0.1)  # type: ignore[call-arg,union-attr]
    axes = []
    for k, name in enumerate(panels):
        ax: Any = fig.add_subplot(nrows, ncols, k + 1, projection="polar")
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)  # clockwise, like a clock
        ax.grid(False)
        ax.spines["polar"].set_visible(False)
        if name:
            ax.set_title(name, fontweight="bold", pad=20)
        axes.append(ax)
    return fig, axes


def _radial_finish(
    fig: Figure,
    axes: List[Any],
    mesh: Any,
    label: str,
    caption: str,
    title: Optional[str],
) -> Figure:
    fig.colorbar(
        mesh, ax=axes, orientation="horizontal", shrink=0.6, aspect=40, label=label
    )
    fig.supxlabel(caption, fontsize=8, alpha=0.8)
    if title:
        fig.suptitle(title, fontweight="bold")
    plt.close(fig)
    return fig


@_themed
def plot_radial(
    data: pd.DataFrame,
    value: str,
    time: str = "date",
    by: Optional[str] = None,
    agg: Optional[str] = None,
    cmap: str = "RdYlBu_r",
    center: Optional[float] = None,
    ncol: int = 2,
    title: Optional[str] = None,
    legend_title: Optional[str] = None,
) -> Figure:
    """Radial calendar: one ring per year, one cell per day.

    The first year is at the centre and the last at the edge. 1 January is
    at 12 o'clock and the year runs clockwise. Days without a value are grey.
    Works for any quantity (temperature, precipitation, a heat index, ...).

    Args:
        data: DataFrame with ``value`` and ``time`` columns, such as
            ``era5ify_*`` output. Hourly output (``date`` and ``hour``) is
            reduced to one value per day with ``agg``.
        value: Column to colour by.
        time: Date or timestamp column.
        by: Optional column. One circle per value (for example a district).
        agg: How to reduce several values in a day: ``"mean"``, ``"sum"``,
            ``"max"`` or ``"min"``. The default sums accumulated ERA5
            variables such as ``tp`` and averages the others.
        cmap: Colour map. For precipitation try ``"Blues"``.
        center: Centre a diverging colour map on this value (for example 0
            for an anomaly).
        ncol: Number of panel columns when ``by`` is set.
        title: Figure title.
        legend_title: Colour bar label. The default is ``value``.

    Returns:
        Matplotlib Figure.

    Example:
        >>> df = era5ify_point("p", ["2m_temperature"], "2015-01-01",
        ...                    "2024-12-31", 19.07, 72.87, frequency="daily")
        >>> plot_radial(df, "2m_temperature").savefig("mumbai.png")
    """
    d = _radial_frame(data, value, time, by, None)
    d["t"] = d["t"].dt.normalize()
    g = d.groupby(["panel", "t"])["value"]
    agg = agg or ("sum" if is_sum_var(value) else "mean")
    daily = g.agg(agg).where(g.count() > 0)  # all-missing day stays missing, not 0
    first, last = int(d["t"].dt.year.min()), int(d["t"].dt.year.max())
    panels = sorted(d["panel"].unique())
    norm = _colour_norm(daily, center)
    colours = plt.get_cmap(cmap).with_extremes(bad=MISSING)

    fig, axes = _radial_figure(panels, ncol)
    for ax, name in zip(axes, panels):
        for year in range(first, last + 1):
            days = pd.date_range(f"{year}-01-01", f"{year}-12-31")
            v = daily.reindex(pd.MultiIndex.from_product([[name], days]))
            # leap years also span the full circle
            theta = np.linspace(0, 2 * np.pi, len(days) + 1)
            ring = year - first + 1 + HOLE
            mesh = ax.pcolormesh(
                theta, [ring - 0.45, ring + 0.45],
                np.ma.masked_invalid(v.to_numpy(dtype=float))[None, :],
                cmap=colours, norm=norm, shading="flat",
            )  # fmt: skip
        ax.set_ylim(0, last - first + 1.5 + HOLE)
        ax.set_xticks((np.arange(12) + 0.5) * 2 * np.pi / 12, MONTH_LABELS)
        ax.set_yticks([])
    span = f"{first} at the centre, {last} at the edge" if last > first else first
    return _radial_finish(
        fig, axes, mesh, legend_title or value,
        f"One ring per year: {span}. Grey: no data.", title,
    )  # fmt: skip


@_themed
def plot_radial_hourly(
    data: pd.DataFrame,
    value: str,
    time: str = "date",
    by: Optional[str] = None,
    rings: str = "month",
    tz: Optional[str] = None,
    accumulated: Optional[bool] = None,
    cmap: str = "RdYlBu_r",
    center: Optional[float] = None,
    ncol: int = 2,
    title: Optional[str] = None,
    legend_title: Optional[str] = None,
) -> Figure:
    """24-hour clock: the angle is the hour of the day.

    Midnight is at 12 o'clock and noon at 6 o'clock, so the day runs
    clockwise like a clock face. With ``rings="month"`` each ring is a
    calendar month (January at the centre, December at the edge) and each
    cell is the mean for that hour over all days of that month in all years:
    the daily cycle and how it changes with the seasons. With
    ``rings="day"`` each ring is one date.

    Args:
        data: Hourly DataFrame with ``value`` and ``time`` columns, such as
            ``era5ify_*(..., frequency="hourly")`` output (``date`` and
            ``hour`` columns are combined).
        value: Column to colour by.
        time: Date or timestamp column.
        by: Optional column. One clock per value.
        rings: ``"month"`` or ``"day"``.
        tz: Time zone for the hour of day, such as ``"Asia/Kolkata"``.
            Times without a time zone are taken as UTC, as in ERA5. The
            default draws UTC hours.
        accumulated: Each value is the total of the hour that ends at its
            time, as ERA5 precipitation; otherwise a reading centred in its
            cell. The default is True for accumulated ERA5 variables (``tp``).
        cmap: Colour map.
        center: Centre a diverging colour map on this value.
        ncol: Number of panel columns when ``by`` is set.
        title: Figure title.
        legend_title: Colour bar label. The default is ``value``.

    Returns:
        Matplotlib Figure.
    """
    if rings not in ("month", "day"):
        raise ValueError('rings must be "month" or "day"')
    d = _radial_frame(data, value, time, by, tz)
    if accumulated is None:
        accumulated = is_sum_var(value)
    # a cell starts 30 min before a reading, or 60 min before an hourly total
    start = d["t"] - pd.Timedelta(minutes=60 if accumulated else 30)
    if start.dt.minute.nunique() == 1:
        offset = start.iloc[0].minute / 60  # cells start this far past the hour
    else:  # mixed minutes, such as 15-minute data: whole clock hours
        start, offset = (start + pd.Timedelta(minutes=30)).dt.floor("h"), 0.0
    d["t"] = start
    d["hour"] = start.dt.hour
    if rings == "month":
        d["ring"] = d["t"].dt.month
        ring_keys: List[Any] = list(range(1, 13))
        starts = list(range(12))
        labels = MONTH_LABELS
        what = "One ring per month (January at the centre): mean of each hour"
    else:
        d["ring"] = d["t"].dt.tz_localize(None).dt.normalize()
        ring_keys = list(pd.date_range(d["ring"].min(), d["ring"].max()))
        yearly = len(ring_keys) > 366  # one label per year, not per month
        starts = [
            i for i, k in enumerate(ring_keys)
            if k.day == 1 and (k.month == 1 or not yearly)
        ] or [0]  # fmt: skip
        labels = [ring_keys[i].strftime("%Y" if yearly else "%b") for i in starts]
        what = "One ring per day, first day at the centre"
    cells = d.groupby(["panel", "ring", "hour"])["value"].mean()
    panels = sorted(d["panel"].unique())
    norm = _colour_norm(cells, center)
    colours = plt.get_cmap(cmap).with_extremes(bad=MISSING)
    # 4 sub-cells per hour round off month rings
    sub = 4 if rings == "month" else 1
    theta = (np.linspace(0, 24, 24 * sub + 1) + offset) * np.pi / 12
    r = np.arange(len(ring_keys) + 1) + HOLE

    fig, axes = _radial_figure(panels, ncol)
    for ax, name in zip(axes, panels):
        index = pd.MultiIndex.from_product([[name], ring_keys, range(24)])
        grid = cells.reindex(index).to_numpy(dtype=float).reshape(-1, 24)
        mesh = ax.pcolormesh(
            theta, r, np.ma.masked_invalid(np.repeat(grid, sub, axis=1)),
            cmap=colours, norm=norm, shading="flat", rasterized=rings == "day",
        )  # fmt: skip
        ax.set_ylim(0, r[-1])
        hours = np.arange(0, 24, 3)
        ax.set_xticks(hours * np.pi / 12, [f"{h:02d}:00" for h in hours])
        # quarter-day spokes help read the hour
        for h in (0, 6, 12, 18):
            ax.plot(
                [h * np.pi / 12] * 2, [HOLE, r[-1]], color="white", lw=0.6, alpha=0.7
            )
        ax.set_yticks(r[starts] + 0.5, labels, fontsize=6)
        ax.set_rlabel_position(0)
        for label in ax.get_yticklabels():
            label.set_bbox({"facecolor": "white", "alpha": 0.6, "pad": 0.5, "lw": 0})
    zone = tz or "UTC"
    return _radial_finish(
        fig, axes, mesh, legend_title or value,
        f"Hour of day ({zone}) clockwise from midnight at the top.\n{what}. "
        "Grey: no data.", title,
    )  # fmt: skip
