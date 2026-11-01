"""plot_radial and plot_radial_hourly."""

import numpy as np
import pandas as pd
import pytest

from varunayan import plot_radial, plot_radial_hourly


def _hourly() -> pd.DataFrame:
    # era5ify_*(frequency="hourly") shape: date + hour (UTC)
    return pd.DataFrame(
        {
            "date": ["2023-01-01"] * 3 + ["2024-12-31"],
            "hour": [0, 1, 2, 23],
            "tp": [1.0, 2.0, 3.0, 4.0],
        }
    )


def test_plot_radial_one_ring_per_year_and_agg_per_day():
    fig = plot_radial(_hourly(), "tp", title="Rain")  # tp is summed by default
    ax = fig.axes[0]
    rings = ax.collections
    assert len(rings) == 2  # 2023 and 2024
    first = rings[0].get_array().ravel()
    assert first[0] == 6.0 and first.mask[1]  # 1 Jan summed, 2 Jan missing
    assert rings[1].get_array().size == 366  # leap year
    assert rings[1].get_array().ravel()[-1] == 4.0
    assert fig._suptitle.get_text() == "Rain"


def test_plot_radial_panel_per_group_and_center():
    df = pd.DataFrame(
        {"date": ["2024-03-01"] * 2, "city": ["B", "A"], "anom": [-1.0, 3.0]}
    )
    fig = plot_radial(df, "anom", by="city", center=0)
    polar = [ax for ax in fig.axes if ax.name == "polar"]
    assert [ax.get_title() for ax in polar] == ["A", "B"]
    norm = polar[0].collections[0].norm
    assert (norm.vmin, norm.vmax) == (-3.0, 3.0)


def test_plot_radial_hourly_month_rings_and_time_zone():
    fig = plot_radial_hourly(_hourly(), "tp", tz="Asia/Kolkata", accumulated=False)
    grid = fig.axes[0].collections[0].get_array().reshape(12, 96)
    hours = grid[:, ::4]  # one column per hour
    # 00:00 UTC on 1 Jan is 05:30 IST: January ring, hour 5
    assert hours[0, 5] == 1.0 and hours[0, 7] == 3.0
    # 23:00 UTC on 31 Dec 2024 is 04:30 IST on 1 Jan 2025
    assert hours[0, 4] == 4.0
    assert hours.mask[11].all()  # no December values in IST


def test_plot_radial_hourly_day_rings_centre_each_reading():
    fig = plot_radial_hourly(_hourly(), "tp", rings="day", accumulated=False)
    grid = fig.axes[0].collections[0].get_array().reshape(-1, 24)  # 1 cell per hour
    # 00:00 on 1 Jan fills 23:30-00:30, so the first ring is 31 Dec 2022
    n_days = (pd.Timestamp("2024-12-31") - pd.Timestamp("2022-12-31")).days + 1
    assert grid.shape[0] == n_days
    assert grid[0, 23] == 1.0 and grid[1, 0] == 2.0 and grid[1, 1] == 3.0
    with pytest.raises(ValueError):
        plot_radial_hourly(_hourly(), "tp", rings="week")


def test_plot_radial_hourly_accumulated_fills_the_hour_before():
    # rain stamped 12:00 UTC fell 11:00-12:00 UTC, 16:30-17:30 IST
    rain = pd.DataFrame({"time": ["2023-07-01 12:00"], "tp": [5.0]})
    fig = plot_radial_hourly(
        rain, "tp", time="time", tz="Asia/Kolkata"
    )  # tp is accumulated by default
    mesh = fig.axes[0].collections[0]
    hours = mesh.get_array().reshape(12, 96)[:, ::4]
    assert hours[6, 16] == 5.0 and hours.count() == 1  # July, cell from 16:30
    first_edge = mesh.get_coordinates()[0, 0, 0]
    assert first_edge == pytest.approx(0.5 * np.pi / 12)  # cells start at :30


def test_fonts_skip_families_without_a_bold_face(monkeypatch):
    from types import SimpleNamespace

    from matplotlib import font_manager

    from varunayan.plot import _fonts_with_bold

    fake = [
        SimpleNamespace(name="Helvetica", weight=400),  # .ttc read as regular only
        SimpleNamespace(name="Arial", weight=400),
        SimpleNamespace(name="Arial", weight="bold"),
    ]
    monkeypatch.setattr(font_manager.fontManager, "ttflist", fake)
    assert _fonts_with_bold() == ["Arial"]
