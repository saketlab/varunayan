"""Matplotlib plots matching the R ggplot2 functions; each returns a closed Figure."""

import calendar
from typing import Any, List, Optional, Sequence, Tuple, Union

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, Colormap, ListedColormap, LogNorm, Normalize
from matplotlib.ticker import MaxNLocator
from matplotlib.figure import Figure

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


def _subplots(*args: Any, **kwargs: Any) -> Tuple[Figure, Any]:
    kwargs.setdefault("dpi", 150)
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
            lim = float((values - center).abs().max())
            norm = Normalize(vmin=center - lim, vmax=center + lim)
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
    im = ax.imshow(mat.to_numpy(dtype=float), aspect="auto", cmap=cmap)
    cols: List[str] = [
        MONTH_LABELS[int(c) - 1] if x == "month" else str(c) for c in mat.columns
    ]
    ax.set_xticks(
        range(mat.shape[1]), cols, rotation=45 if x != "month" else 0, ha="right"
    )
    ax.set_yticks(range(mat.shape[0]), [str(i) for i in mat.index])
    if annotate:
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                ax.text(
                    j, i, f"{mat.iat[i, j]:.2f}", ha="center", va="center", fontsize=7
                )
    fig.colorbar(im, ax=ax, shrink=0.8, label=value or "")
    return _finish(fig, title)
