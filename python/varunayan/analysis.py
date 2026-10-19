"""Analysis helpers over long DataFrames, mirroring the R package."""

import logging
import os
from typing import List, Optional, Sequence, Tuple, Union

import geopandas as gpd
import numpy as np
import pandas as pd
import requests

from .cache import get_cache_dir

logger = logging.getLogger(__name__)

Columns = Union[str, Sequence[str], None]

INDIA_BOUNDARY_URLS = {
    "state": "https://geo.bharatviz.org/geojsons/admin/India-geodata-lgd-states.geojson",
    "district": "https://geo.bharatviz.org/geojsons/admin/India-geodata-lgd-districts.geojson",
}


def _as_list(cols: Columns) -> List[str]:
    if cols is None:
        return []
    if isinstance(cols, str):
        return [cols]
    return list(cols)


def _with_date(df: pd.DataFrame) -> pd.DataFrame:
    """Add a ``date`` column (first of month) when ``year`` and ``month`` exist."""
    if {"year", "month"} <= set(df.columns) and "date" not in df.columns:
        df = df.assign(date=pd.to_datetime(df[["year", "month"]].assign(day=1)))
    return df


def load_india_boundaries(level: str = "state") -> gpd.GeoDataFrame:
    """Load India LGD state or district boundaries (EPSG:4326).

    The file is downloaded once from geo.bharatviz.org and cached.

    Args:
        level: ``"state"`` or ``"district"``.

    Returns:
        GeoDataFrame with ``state_name`` (and ``district_name`` for districts).

    Raises:
        ValueError: If ``level`` is unknown.
    """
    if level not in INDIA_BOUNDARY_URLS:
        raise ValueError(f"level must be one of {sorted(INDIA_BOUNDARY_URLS)}")
    path = os.path.join(get_cache_dir(), f"india_lgd_{level}s.geojson")
    if not os.path.exists(path):
        logger.info("Downloading India %s boundaries", level)
        resp = requests.get(INDIA_BOUNDARY_URLS[level], timeout=300)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(resp.content)
    gdf = gpd.read_file(path)
    return gdf.to_crs("EPSG:4326") if gdf.crs else gdf.set_crs("EPSG:4326")


def spatial_mean(
    data: pd.DataFrame,
    value: str,
    by: Columns = ("year", "month"),
    weight: Optional[str] = "coslat",
    lat_col: str = "latitude",
) -> pd.DataFrame:
    """Average ``value`` over grid points for each group in ``by``.

    Args:
        data: Long DataFrame with ``lat_col`` and the ``by`` columns.
        value: Column to average.
        by: Grouping columns, for example ``("year", "month")`` or ``"year"``.
        weight: ``"coslat"`` weights each point by cos(latitude), so that
            points near the poles count less. ``None`` gives a plain mean.
        lat_col: Latitude column.

    Returns:
        DataFrame with the ``by`` columns and ``value``. A ``date`` column is
        added when ``by`` holds ``year`` and ``month``.
    """
    groups = _as_list(by)
    df = data.dropna(subset=[value])
    if weight == "coslat":
        w = np.cos(np.deg2rad(df[lat_col]))
    elif weight is None:
        w = pd.Series(1.0, index=df.index)
    else:
        raise ValueError("weight must be 'coslat' or None")
    tmp = pd.DataFrame({"_wv": df[value] * w, "_w": w})
    if not groups:
        return pd.DataFrame({value: [tmp["_wv"].sum() / tmp["_w"].sum()]})
    tmp[groups] = df[groups]
    out = tmp.groupby(groups, as_index=False)[["_wv", "_w"]].sum()
    out[value] = out["_wv"] / out["_w"]
    return _with_date(out[groups + [value]])


def compare(
    data: pd.DataFrame,
    x: str,
    y: str,
    by: Columns = None,
) -> pd.DataFrame:
    """Agreement statistics between two columns, optionally per group.

    Rows where ``x`` or ``y`` is missing are dropped first.

    Args:
        data: DataFrame that holds both series, for example after a merge.
        x: First column (for example the reference dataset).
        y: Second column.
        by: Optional grouping columns, for example ``"state_name"``.

    Returns:
        DataFrame with ``n``, ``r`` (Pearson), ``bias`` (mean of y - x) and
        ``rmse`` for each group.
    """
    groups = _as_list(by)
    df = data.dropna(subset=[x, y])

    def _stats(g: pd.DataFrame) -> pd.Series:
        d = g[y] - g[x]
        r = g[x].corr(g[y]) if len(g) > 1 else np.nan
        return pd.Series(
            {
                "n": len(g),
                "r": r,
                "bias": d.mean(),
                "rmse": float(np.sqrt((d**2).mean())),
            }
        )

    if not groups:
        return _stats(df).to_frame().T.astype({"n": int})
    out = df.groupby(groups)[[x, y]].apply(_stats).reset_index()
    return out.astype({"n": int})


def cross_correlation(
    x: Sequence[float], y: Sequence[float], max_lag: int = 12
) -> pd.DataFrame:
    """Cross-correlation of two equal-length series, as R ``stats::ccf``.

    ``r`` at lag ``k`` estimates cor(x[t + k], y[t]). A peak at a negative lag
    means that ``x`` changes before ``y``.

    Args:
        x: First series.
        y: Second series, same length as ``x``.
        max_lag: Largest lag to return, in steps.

    Returns:
        DataFrame with ``lag`` (-max_lag to max_lag) and ``r``.

    Raises:
        ValueError: If the series have different lengths.
    """
    xa: np.ndarray = np.asarray(x, dtype=float)
    ya: np.ndarray = np.asarray(y, dtype=float)
    if len(xa) != len(ya):
        raise ValueError("x and y must have the same length")
    n = len(xa)
    xc, yc = xa - xa.mean(), ya - ya.mean()
    denom = np.sqrt((xc**2).sum() * (yc**2).sum())
    lags = np.arange(-max_lag, max_lag + 1)
    r = [
        (
            (xc[k:] * yc[: n - k]).sum() / denom
            if k >= 0
            else (xc[: n + k] * yc[-k:]).sum() / denom
        )
        for k in lags
    ]
    return pd.DataFrame({"lag": lags, "r": r})


def anomaly(
    data: pd.DataFrame,
    value: str,
    baseline: Optional[Tuple[int, int]] = None,
    year_col: str = "year",
) -> pd.Series:
    """Departure of ``value`` from its mean over a baseline period.

    Args:
        data: DataFrame with ``value`` (and ``year_col`` if a baseline is set).
        value: Column to use.
        baseline: Optional ``(first_year, last_year)``. Default: all rows.
        year_col: Year column for the baseline.

    Returns:
        Series of anomalies, aligned with ``data``.
    """
    ref = data[value]
    if baseline is not None:
        ref = ref[data[year_col].between(*baseline)]
    return data[value] - ref.mean()


def seasonal_cycle(data: pd.DataFrame, value: str, by: Columns = None) -> pd.DataFrame:
    """Mean of ``value`` for each calendar month (and each group in ``by``).

    Args:
        data: DataFrame with a ``month`` column (1-12).
        value: Column to average.
        by: Optional grouping columns, for example ``"country"``.

    Returns:
        DataFrame with the ``by`` columns, ``month`` and ``value``.
    """
    groups = _as_list(by) + ["month"]
    return data.groupby(groups, as_index=False)[[value]].mean()


def peak_month(
    data: pd.DataFrame,
    value: str,
    by: Columns = ("latitude", "longitude"),
) -> pd.DataFrame:
    """Month of the largest long-term mean of ``value`` for each group.

    Args:
        data: DataFrame with ``month`` and the ``by`` columns.
        value: Column to use, for example monthly precipitation.
        by: Grouping columns. Default: each grid point.

    Returns:
        DataFrame with the ``by`` columns, ``peak_month`` (1-12),
        ``peak_value`` and ``annual_total`` (sum of the 12 monthly means).
    """
    groups = _as_list(by)
    clim = seasonal_cycle(data, value, by=groups)
    idx = clim.groupby(groups)[value].idxmax()
    peak = clim.loc[idx, groups + ["month", value]].rename(
        columns={"month": "peak_month", value: "peak_value"}
    )
    total = clim.groupby(groups, as_index=False)[[value]].sum()
    total = total.rename(columns={value: "annual_total"})
    return peak.merge(total, on=groups).reset_index(drop=True)


def seasonal_stat(
    data: pd.DataFrame,
    value: str,
    months: Sequence[int],
    how: str = "sum",
    by: Columns = ("latitude", "longitude"),
) -> pd.DataFrame:
    """Seasonal total or mean of ``value``, averaged over years.

    For each group and year the function takes the ``how`` of the selected
    months. Then it calculates the mean over the years.

    Args:
        data: DataFrame with ``year``, ``month`` (or ``date``) and ``by``.
        value: Column to use.
        months: Months of the season, for example ``[6, 7, 8]``.
        how: ``"sum"`` (seasonal total) or ``"mean"``.
        by: Grouping columns. Default: each grid point.

    Returns:
        DataFrame with the ``by`` columns and ``value``.
    """
    if how not in ("sum", "mean"):
        raise ValueError("how must be 'sum' or 'mean'")
    df = data
    if "month" not in df.columns or "year" not in df.columns:
        dates = pd.to_datetime(df["date"])
        df = df.assign(year=dates.dt.year, month=dates.dt.month)
    df = df[df["month"].isin(list(months))]
    groups = _as_list(by)
    per_year = df.groupby(groups + ["year"], as_index=False)[[value]].agg(how)
    return per_year.groupby(groups, as_index=False)[[value]].mean()


def regrid(
    data: pd.DataFrame,
    value: str,
    resolution: float,
    by: Columns = None,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
) -> pd.DataFrame:
    """Average ``value`` onto a coarser regular grid.

    Each point goes into the cell of size ``resolution`` that contains it.
    The output coordinates are the cell centres, so a 0.5 degree grid has
    centres at x.25 and x.75, the same as CRU TS.

    Args:
        data: DataFrame with latitude and longitude columns.
        value: Column to average.
        resolution: Target cell size in degrees.
        by: Optional extra grouping columns, for example ``"year"``.
        lat_col: Latitude column.
        lon_col: Longitude column.

    Returns:
        DataFrame with ``lat_col``, ``lon_col``, the ``by`` columns and ``value``.
    """
    half = resolution / 2

    def _centre(v: pd.Series) -> pd.Series:
        # The small offset keeps 0.3 / 0.1 = 2.9999... in cell 3.
        cells = np.round(np.floor(v / resolution + 1e-9) * resolution + half, 6)
        return pd.Series(cells, index=v.index)

    df = data.assign(
        **{lat_col: _centre(data[lat_col]), lon_col: _centre(data[lon_col])}
    )
    groups = [lat_col, lon_col] + _as_list(by)
    return df.groupby(groups, as_index=False)[[value]].mean()
