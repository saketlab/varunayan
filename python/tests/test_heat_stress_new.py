"""Heat stress functions: Python vs R reference values."""

import numpy as np
import pytest

from varunayan.heat_stress import (
    heat_index_from_dewpoint,
    utci_sparse,
    wet_bulb_from_dewpoint,
)

UTCI_SPARSE_CASES = [
    (30, 50, 2, 50, 34.14762),
    (25, 30, 5, 80, 23.38699),
    (40, 70, 1, 30, 47.83232),
    (10, 15, 3, 60, 6.622718),
    (-5, 0, 10, 40, -32.32655),
]


@pytest.mark.parametrize("ta,tmrt,va,rh,expected", UTCI_SPARSE_CASES)
def test_utci_sparse_vs_r(ta, tmrt, va, rh, expected):
    result = utci_sparse(ta, tmrt, va, rh)
    assert (
        abs(result - expected) < 0.01
    ), f"utci_sparse({ta},{tmrt},{va},{rh})={result}, R={expected}"


def test_utci_sparse_vectorized():
    ta = np.array([30, 25, 40])
    tmrt = np.array([50, 30, 70])
    va = np.array([2, 5, 1])
    rh = np.array([50, 80, 30])
    result = utci_sparse(ta, tmrt, va, rh)
    expected = np.array([34.14762, 23.38699, 47.83232])
    np.testing.assert_allclose(result, expected, atol=0.01)


def test_utci_sparse_wind_clamping():
    low = utci_sparse(30, 50, 0.1, 50)
    at_min = utci_sparse(30, 50, 0.5, 50)
    assert abs(low - at_min) < 1e-10, "Wind below 0.5 should be clamped to 0.5"


WET_BULB_CASES = [
    (35, 25, 27.80227),
    (30, 20, 23.17424),
    (25, 15, 18.5848),
]


@pytest.mark.parametrize("temp,dp,expected", WET_BULB_CASES)
def test_wet_bulb_from_dewpoint_vs_r(temp, dp, expected):
    result = wet_bulb_from_dewpoint(temp, dp)
    assert (
        abs(result - expected) < 0.01
    ), f"wet_bulb_from_dewpoint({temp},{dp})={result}, R={expected}"


HEAT_INDEX_CASES = [
    (35, 25, 43.31715),
    (30, 20, 31.90151),
    (40, 30, 60.50336),
]


@pytest.mark.parametrize("temp,dp,expected", HEAT_INDEX_CASES)
def test_heat_index_from_dewpoint_vs_r(temp, dp, expected):
    result = heat_index_from_dewpoint(temp, dp)
    assert (
        abs(result - expected) < 0.01
    ), f"heat_index_from_dewpoint({temp},{dp})={result}, R={expected}"
