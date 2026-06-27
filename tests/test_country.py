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
