from typing import Dict, List
from unittest.mock import patch

import pytest
from pytest import CaptureFixture

from varunayan.search_and_desc.search_and_desc_functions import (
    _process_pressure_dataset,  # type: ignore
)
from varunayan.search_and_desc.search_and_desc_functions import (
    _process_single_dataset,  # type: ignore
)
from varunayan.search_and_desc.search_and_desc_functions import (
    describe_variables,
    get_available_datasets,
    get_pressure_levels_dataset,
    get_single_levels_dataset,
    search_variable,
)

# Test data for mocking
MOCK_SINGLE_DATASET = {
    "temperature_and_pressure": [
        {"name": "temp", "description": "Temperature variable"},
        {"name": "pressure", "description": "Pressure variable"},
    ],
    "wind_variables": [{"name": "wind_speed", "description": "Wind speed variable"}],
}

MOCK_PRESSURE_DATASET = [
    {"name": "pressure_lev1", "description": "Pressure level 1"},
    {"name": "pressure_lev2", "description": "Pressure level 2"},
]


# Fixtures for common test data
@pytest.fixture
def single_level_processed():
    return [
        {
            "name": "temp",
            "description": "Temperature variable",
            "category": "temperature_and_pressure",
            "dataset": "single",
        },
        {
            "name": "pressure",
            "description": "Pressure variable",
            "category": "temperature_and_pressure",
            "dataset": "single",
        },
        {
            "name": "wind_speed",
            "description": "Wind speed variable",
            "category": "wind_variables",
            "dataset": "single",
        },
    ]


@pytest.fixture
def pressure_level_processed():
    return [
        {
            "name": "pressure_lev1",
            "description": "Pressure level 1",
            "category": "pressure_levels",
            "dataset": "pressure",
        },
        {
            "name": "pressure_lev2",
            "description": "Pressure level 2",
            "category": "pressure_levels",
            "dataset": "pressure",
        },
    ]


# Tests for get_available_datasets
def test_get_available_datasets():
    assert get_available_datasets() == ["single", "pressure", "all"]


# Tests for get_single_levels_dataset with mocking
@patch(
    "varunayan.search_and_desc.single_levels_variables.temperature_and_pressure",
    MOCK_SINGLE_DATASET["temperature_and_pressure"],
)
@patch(
    "varunayan.search_and_desc.single_levels_variables.wind_variables",
    MOCK_SINGLE_DATASET["wind_variables"],
)
def test_get_single_levels_dataset():
    result = get_single_levels_dataset()
    assert isinstance(result, dict)
    assert "temperature_and_pressure" in result
    assert "wind_variables" in result
    assert len(result["temperature_and_pressure"]) == 2
    assert len(result["wind_variables"]) == 1


# Tests for get_pressure_levels_dataset with mocking
@patch(
    "varunayan.search_and_desc.pressure_levels_variables.pressure_level_variables",
    MOCK_PRESSURE_DATASET,
)
def test_get_pressure_levels_dataset():
    result = get_pressure_levels_dataset()
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["name"] == "pressure_lev1"


# Tests for _process_single_dataset
def test_process_single_dataset(single_level_processed: List[Dict[str, str]]):
    with patch(
        "varunayan.search_and_desc.search_and_desc_functions.get_single_levels_dataset",
        return_value=MOCK_SINGLE_DATASET,
    ):
        result = _process_single_dataset("single")
        assert len(result) == 3
        assert result[0]["category"] == "temperature_and_pressure"
        assert result[2]["category"] == "wind_variables"
        assert all("dataset" in var for var in result)


# Tests for _process_pressure_dataset
def test_process_pressure_dataset(pressure_level_processed: List[Dict[str, str]]):
    with patch(
        "varunayan.search_and_desc.search_and_desc_functions.get_pressure_levels_dataset",
        return_value=MOCK_PRESSURE_DATASET,
    ):
        result = _process_pressure_dataset("pressure")
        assert len(result) == 2
        assert all(var["category"] == "pressure_levels" for var in result)
        assert all("dataset" in var for var in result)


# Tests for describe_variables
def test_describe_variables_single(
    capsys: CaptureFixture[str], single_level_processed: List[Dict[str, str]]
):
    with patch(
        "varunayan.search_and_desc.search_and_desc_functions._process_single_dataset",
        return_value=single_level_processed,
    ):
        describe_variables(["temp", "wind_speed"], "single")
        captured = capsys.readouterr()
        assert "=== Variable Descriptions (SINGLE LEVELS) ===" in captured.out
        assert "temp:" in captured.out
        assert "wind_speed:" in captured.out
        assert "Variable not found" not in captured.out


def test_describe_variables_not_found(
    capsys: CaptureFixture[str], single_level_processed: List[Dict[str, str]]
):
    with patch(
        "varunayan.search_and_desc.search_and_desc_functions._process_single_dataset",
        return_value=single_level_processed,
    ):
        describe_variables(["nonexistent"], "single")
        captured = capsys.readouterr()
        assert "nonexistent:" in captured.out
        assert "Variable not found" in captured.out


def test_describe_variables_all(
    capsys: CaptureFixture[str],
    single_level_processed: List[Dict[str, str]],
    pressure_level_processed: List[Dict[str, str]],
):
    with patch(
        "varunayan.search_and_desc.search_and_desc_functions._process_single_dataset",
        return_value=single_level_processed,
    ), patch(
        "varunayan.search_and_desc.search_and_desc_functions._process_pressure_dataset",
        return_value=pressure_level_processed,
    ):
        describe_variables(["temp", "pressure_lev1"], "all")
        captured = capsys.readouterr()
        assert "=== Variable Descriptions (ALL LEVELS) ===" in captured.out
        assert "temp:" in captured.out
        assert "pressure_lev1:" in captured.out
        assert "Dataset: single" in captured.out
        assert "Dataset: pressure" in captured.out


def test_describe_variables_invalid_type():
    with pytest.raises(ValueError) as excinfo:
        describe_variables(["temp"], "invalid")
    assert "dataset_type must be one of:" in str(excinfo.value)


# Tests for search_variable
def test_search_variable_single(
    capsys: CaptureFixture[str], single_level_processed: List[Dict[str, str]]
):
    with patch(
        "varunayan.search_and_desc.search_and_desc_functions._process_single_dataset",
        return_value=single_level_processed,
    ):
        search_variable("temp", "single")
        captured = capsys.readouterr()
        assert "=== SEARCH RESULTS (SINGLE LEVELS) ===" in captured.out
        assert "Pattern: 'temp'" in captured.out
        assert "1. temp" in captured.out
        assert "Temperature variable" in captured.out


def test_search_variable_all(
    capsys: CaptureFixture[str],
    single_level_processed: List[Dict[str, str]],
    pressure_level_processed: List[Dict[str, str]],
):
    with patch(
        "varunayan.search_and_desc.search_and_desc_functions._process_single_dataset",
        return_value=single_level_processed,
    ), patch(
        "varunayan.search_and_desc.search_and_desc_functions._process_pressure_dataset",
        return_value=pressure_level_processed,
    ):
        search_variable("pressure", "all")
        captured = capsys.readouterr()
        assert "=== SEARCH RESULTS (ALL LEVELS) ===" in captured.out
        assert "Pattern: 'pressure'" in captured.out
        assert "pressure (from single levels)" in captured.out
        assert "pressure_lev1 (from pressure levels)" in captured.out


def test_search_variable_no_pattern(
    capsys: CaptureFixture[str], single_level_processed: List[Dict[str, str]]
):
    with patch(
        "varunayan.search_and_desc.search_and_desc_functions._process_single_dataset",
        return_value=single_level_processed,
    ):
        search_variable(None, "single")
        captured = capsys.readouterr()
        assert "=== ALL VARIABLES (SINGLE LEVELS) ===" in captured.out
        assert "Total variables found: 3" in captured.out


def test_search_variable_no_matches(
    capsys: CaptureFixture[str], single_level_processed: List[Dict[str, str]]
):
    with patch(
        "varunayan.search_and_desc.search_and_desc_functions._process_single_dataset",
        return_value=single_level_processed,
    ):
        search_variable("nonexistent", "single")
        captured = capsys.readouterr()
        assert "No variables found matching the pattern." in captured.out


def test_search_variable_invalid_type():
    with pytest.raises(ValueError) as excinfo:
        search_variable("temp", "invalid")
    assert "dataset_type must be one of:" in str(excinfo.value)
