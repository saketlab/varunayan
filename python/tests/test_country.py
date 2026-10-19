"""Country resolution: name/alias/ISO matching against Natural Earth."""

import pytest
import geopandas as gpd

from varunayan.country import _resolve_country, _ALIASES


def test_resolve_india():
    poly = _resolve_country("India")
    assert len(poly) == 1
    assert poly.iloc[0]["ISO_A3"] == "IND"


def test_resolve_usa_alias():
    poly = _resolve_country("USA")
    assert len(poly) == 1


def test_resolve_uk_alias():
    poly = _resolve_country("UK")
    assert len(poly) == 1


def test_resolve_iso3():
    poly = _resolve_country("DEU")
    assert len(poly) == 1
    assert poly.iloc[0]["NAME"] == "Germany"


def test_resolve_iso2():
    poly = _resolve_country("FR")
    assert len(poly) == 1


def test_resolve_unknown_raises():
    with pytest.raises(ValueError, match="not found"):
        _resolve_country("Narnia")


def test_resolve_geodataframe_passthrough():
    gdf = gpd.GeoDataFrame({"geometry": []})
    result = _resolve_country(gdf)
    assert result is gdf


def test_resolve_partial_match():
    poly = _resolve_country("Bangladesh")
    assert len(poly) == 1


def test_aliases_cover_common_names():
    expected = {"USA", "US", "UK", "Russia", "South Korea", "North Korea"}
    assert expected.issubset(set(_ALIASES.keys()))


def _long_monthly(cells, months):
    """Long monthly ERA5 output; ``cells`` maps (lat, lon) -> {variable: value}."""
    import pandas as pd

    rows = []
    for year, month in months:
        for (lat, lon), values in cells.items():
            for var, val in values.items():
                rows.append(
                    {
                        "datetime": pd.Timestamp(year=year, month=month, day=1),
                        "latitude": lat,
                        "longitude": lon,
                        "variable": var,
                        "value": val + month,
                        "year": year,
                        "month": month,
                    }
                )
    return pd.DataFrame(rows)


def test_country_temperature_coslat_weighted_and_pivoted():
    from unittest.mock import patch

    import math

    from shapely.geometry import box

    from varunayan.country import get_era5_country_temperature

    polygon = gpd.GeoDataFrame(geometry=[box(0.0, -1.0, 10.0, 61.0)], crs="EPSG:4326")
    mx = "maximum_2m_temperature_since_previous_post_processing"
    cells = {
        (0.0, 5.0): {"2m_temperature": 10.0, mx: 30.0},
        (60.0, 5.0): {"2m_temperature": 20.0, mx: 40.0},
        # Outside the polygon: must be dropped
        (30.0, 20.0): {"2m_temperature": 1000.0, mx: 1000.0},
    }
    long = _long_monthly(cells, [(2020, 2), (2020, 1)])

    with patch("varunayan.country.era5ify_bbox", return_value=long) as mock_bbox:
        out = get_era5_country_temperature(
            polygon, "2020-01-01", "2020-02-29", variables=["mean", "max", "mean"]
        )

    kwargs = mock_bbox.call_args.kwargs
    assert kwargs["frequency"] == "monthly"
    assert kwargs["variables"] == ["2m_temperature", mx]
    assert kwargs["request_id"] == "custom"
    assert (kwargs["north"], kwargs["south"]) == (61.0, -1.0)
    assert (kwargs["east"], kwargs["west"]) == (10.0, 0.0)

    assert list(out.columns) == ["year", "month", "temperature_max", "temperature_mean"]
    assert list(out["month"]) == [1, 2]
    assert list(out["year"]) == [2020, 2020]

    w0, w60 = math.cos(0.0), math.cos(math.radians(60.0))
    for i, month in enumerate((1, 2)):
        mean = ((10 + month) * w0 + (20 + month) * w60) / (w0 + w60)
        tmax = ((30 + month) * w0 + (40 + month) * w60) / (w0 + w60)
        assert out.loc[i, "temperature_mean"] == pytest.approx(mean)
        assert out.loc[i, "temperature_max"] == pytest.approx(tmax)
    # Not the plain mean
    assert out.loc[0, "temperature_mean"] != pytest.approx(16.0)


def test_country_temperature_short_names_renamed():
    from unittest.mock import patch

    from shapely.geometry import box

    from varunayan.country import get_era5_country_temperature

    polygon = gpd.GeoDataFrame(geometry=[box(0.0, 0.0, 1.0, 1.0)], crs="EPSG:4326")
    long = _long_monthly({(0.5, 0.5): {"t2m": 5.0, "mn2t": -5.0}}, [(2021, 3)])
    with patch("varunayan.country.era5ify_bbox", return_value=long):
        out = get_era5_country_temperature(
            polygon, "2021-03-01", "2021-03-31", variables=["mean", "min"]
        )
    assert list(out.columns) == ["year", "month", "temperature_mean", "temperature_min"]
    assert out.loc[0, "temperature_mean"] == pytest.approx(8.0)
    assert out.loc[0, "temperature_min"] == pytest.approx(-2.0)
