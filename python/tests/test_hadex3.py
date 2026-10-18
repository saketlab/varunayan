"""HadEX3 metadata: Python vs R reference values."""

import pytest

from varunayan.hadex3 import list_hadex3_indices


def test_list_hadex3_indices_total():
    df = list_hadex3_indices()
    assert len(df) == 29


def test_list_hadex3_indices_columns():
    df = list_hadex3_indices()
    assert list(df.columns) == [
        "index",
        "category",
        "description",
        "unit",
        "annual",
        "monthly",
    ]


def test_list_hadex3_indices_first_five():
    df = list_hadex3_indices()
    assert list(df["index"][:5]) == ["TXx", "TXn", "TNx", "TNn", "TX90p"]


def test_list_hadex3_indices_last_five():
    df = list_hadex3_indices()
    assert list(df["index"][-5:]) == ["R95p", "R99p", "R95pTOT", "R99pTOT", "SDII"]


def test_list_hadex3_indices_annual_count():
    df = list_hadex3_indices()
    assert df["annual"].sum() == 29


def test_list_hadex3_indices_monthly_count():
    df = list_hadex3_indices()
    assert df["monthly"].sum() == 18


def test_list_hadex3_indices_filter_annual():
    df = list_hadex3_indices(frequency="annual")
    assert len(df) == 29
    assert df["annual"].all()


def test_list_hadex3_indices_filter_monthly():
    df = list_hadex3_indices(frequency="monthly")
    assert len(df) == 18
    assert df["monthly"].all()


def test_list_hadex3_indices_invalid_frequency():
    with pytest.raises(ValueError, match="frequency must be"):
        list_hadex3_indices(frequency="weekly")
