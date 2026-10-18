"""CRU TS metadata: Python vs R reference values."""

from varunayan.cru_ts import list_cru_ts_variables


def test_list_cru_ts_variables_total():
    df = list_cru_ts_variables()
    assert len(df) == 10


def test_list_cru_ts_variables_columns():
    df = list_cru_ts_variables()
    expected = [
        "variable",
        "name",
        "description",
        "unit",
        "era5_equivalent",
        "hadex3_equivalent",
    ]
    assert list(df.columns) == expected


def test_list_cru_ts_variables_names():
    df = list_cru_ts_variables()
    assert list(df["variable"]) == [
        "tmp",
        "tmx",
        "tmn",
        "dtr",
        "pre",
        "wet",
        "frs",
        "vap",
        "cld",
        "pet",
    ]


def test_list_cru_ts_variables_units():
    df = list_cru_ts_variables()
    assert list(df["unit"]) == [
        "°C",
        "°C",
        "°C",
        "°C",
        "mm/month",
        "days/month",
        "days/month",
        "hPa",
        "%",
        "mm/month",
    ]
