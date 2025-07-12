import pytest
import datetime as dt
import pandas as pd
import xarray as xr
import pandas as pd
from calendar import monthrange
import unittest.mock as mock
import os
import sys
from unittest.mock import MagicMock, patch, Mock

# Block ALL network calls
sys.modules['cdsapi'] = MagicMock()
sys.modules['urllib.request'] = MagicMock()
sys.modules['requests'] = MagicMock()

from eranest.core import (
    ProcessingParams,
    download_with_retry,
    process_time_chunks,
    process_era5_data,
    aggregate_and_save,
    era5ify_geojson,
    era5ify_bbox,
    era5ify_point,
    parse_date,
    validate_inputs,
    adjust_sum_variables,
    SUM_VARS,
)

# Import the download functions
from eranest.download.era5_downloader import (
    download_era5_single_lvl,
    download_era5_pressure_lvl
)

def test_processing_params_initialization(basic_params):
    assert basic_params.request_id == "test_request"
    assert basic_params.variables == ["2m_temperature", "total_precipitation"]
    assert basic_params.start_date == dt.datetime(2020, 1, 1)
    assert basic_params.end_date == dt.datetime(2020, 1, 2)
    assert basic_params.frequency == "hourly"
    assert basic_params.resolution == 0.25


def test_parse_date():
    assert parse_date("2020-01-01") == dt.datetime(2020, 1, 1)
    assert parse_date("2020-1-1") == dt.datetime(2020, 1, 1)
    with pytest.raises(ValueError):
        parse_date("invalid-date")


def test_validate_inputs(basic_params):
    # Should not raise exceptions for valid inputs
    validate_inputs(basic_params)
    
    # Test invalid cases - empty variables
    with pytest.raises(ValueError):
        invalid_params = ProcessingParams(
            request_id="test",
            variables=[],  # Empty variables
            start_date=basic_params.start_date,
            end_date=basic_params.end_date,
            frequency=basic_params.frequency,
            resolution=basic_params.resolution,
            north=basic_params.north,
            south=basic_params.south,
            east=basic_params.east,
            west=basic_params.west
        )
        validate_inputs(invalid_params)
    
    # Test invalid dates - start_date after end_date
    with pytest.raises(ValueError):
        invalid_params = ProcessingParams(
            request_id="test",
            variables=basic_params.variables,
            start_date=dt.datetime(2020, 1, 3),  # After end_date
            end_date=dt.datetime(2020, 1, 2),
            frequency=basic_params.frequency,
            resolution=basic_params.resolution,
            north=basic_params.north,
            south=basic_params.south,
            east=basic_params.east,
            west=basic_params.west
        )
        validate_inputs(invalid_params)

    # Test invalid case - no pressure levels for pressure level data
    with pytest.raises(ValueError):
        invalid_params = ProcessingParams(
            request_id="test",
            variables=basic_params.variables,
            start_date=dt.datetime(2020, 1, 1),
            end_date=dt.datetime(2020, 1, 2),
            frequency=basic_params.frequency,
            resolution=basic_params.resolution,
            north=basic_params.north,
            south=basic_params.south,
            east=basic_params.east,
            west=basic_params.west,
            dataset_type="pressure"
        )
        validate_inputs(invalid_params)
    
    # Test invalid case - no geojson file at directory location
    with pytest.raises(FileNotFoundError):
        invalid_params = ProcessingParams(
            request_id="test",
            variables=basic_params.variables,
            start_date=dt.datetime(2020, 1, 1),
            end_date=dt.datetime(2020, 1, 2),
            frequency=basic_params.frequency,
            resolution=basic_params.resolution,
            geojson_file="yay.json"
        )
        validate_inputs(invalid_params)


def test_download_with_retry_success(basic_params, tmp_path):
    # Setup test file
    test_file = tmp_path / "test_request.zip"
    test_file.touch()

    # Create a mock download function that returns the test file path
    def mock_download_func(**kwargs):
        return str(test_file)

    # Test the download with retry
    result = download_with_retry(mock_download_func, basic_params)
    
    # Verification
    assert result == str(test_file)

def test_download_with_retry_success_mo(basic_params_mo, tmp_path):
    # Setup test file
    test_file = tmp_path / "test_request.zip"
    test_file.touch()

    # Create a mock download function that returns the test file path
    def mock_download_func(**kwargs):
        return str(test_file)

    # Test the download with retry
    result = download_with_retry(mock_download_func, basic_params_mo)
    
    # Verification
    assert result == str(test_file)

def test_download_with_retry_pressure_levels_with_mock(pressure_params, tmp_path):
    # Setup test file
    test_file = tmp_path / "test_request.zip"
    test_file.touch()

    # Option 1: If core.py imports like: from eranest.download import download_era5_pressure_lvl
    # Then patch in core where it's imported:
    with mock.patch('eranest.core.download_era5_pressure_lvl', return_value=str(test_file)) as mock_download:
        from eranest.core import download_era5_pressure_lvl
        result = download_with_retry(download_era5_pressure_lvl, pressure_params)
    
    # Verify the mock was called with pressure_levels
    mock_download.assert_called_once()
    call_args = mock_download.call_args[1]
    print("Call args:", call_args)
    assert 'pressure_levels' in call_args, f"pressure_levels not found in {call_args}"
    assert call_args['pressure_levels'] == pressure_params.pressure_levels
    
    assert result == str(test_file)


@patch('time.sleep')  # Mock sleep to avoid waiting
def test_download_with_retry_failure(mock_sleep, basic_params):
    def failing_download(**kwargs):
        raise Exception("Download failed")
    
    with pytest.raises(Exception):
        download_with_retry(failing_download, basic_params)
    
    assert mock_sleep.call_count > 0


@patch('eranest.core.process_era5_data')
def test_process_time_chunks_no_chunking(mock_process, basic_params):
    mock_process.return_value = pd.DataFrame({"test": [1, 2, 3]})
    
    # Create a mock download function
    def mock_download_func(params):
        return mock_process(params)
    
    result = process_time_chunks(basic_params, None, mock_download_func)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3

@patch('eranest.core.process_era5_data')
def test_process_time_chunks_no_chunking_mo(mock_process, basic_params_mo):
    mock_process.return_value = pd.DataFrame({"test": [1, 2, 3]})
    
    # Create a mock download function
    def mock_download_func(params):
        return mock_process(params)
    
    result = process_time_chunks(basic_params_mo, None, mock_download_func)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3

@patch('time.sleep')
@patch('eranest.core.process_era5_data')
def test_process_time_chunks_with_chunking(mock_process, basic_params):
    mock_process.return_value = pd.DataFrame({"test": [1, 2, 3]})
    
    # Create params that would require chunking (>14 days)
    chunk_params = ProcessingParams(
        request_id=basic_params.request_id,
        variables=basic_params.variables,
        start_date=dt.datetime(2020, 1, 1),
        end_date=dt.datetime(2020, 2, 15),  # >14 days
        frequency=basic_params.frequency,
        resolution=basic_params.resolution,
        north=basic_params.north,
        south=basic_params.south,
        east=basic_params.east,
        west=basic_params.west
    )
    
    # Create a mock download function
    def mock_download_func(params, chunk_num=None, total_chunks=None):
        return mock_process(params)
    
    result = process_time_chunks(chunk_params, None, mock_download_func)
    assert isinstance(result, pd.DataFrame)

@patch('eranest.core.save_results')
@patch('eranest.core.aggregate_by_frequency')
def test_aggregate_and_save(mock_agg, mock_save, basic_params, temp_dir):
    test_df = pd.DataFrame({
        "valid_time": pd.to_datetime(["2020-01-01", "2020-01-02"]),
        "latitude": [37.75, 37.75],
        "longitude": [-122.25, -122.25],
        "t2m": [280, 281],
        "tp": [0, 0.1]
    })
    
    # Mock aggregation to return the same dataframe
    mock_agg.return_value = (test_df, pd.DataFrame())
    
    result = aggregate_and_save(basic_params, test_df)
    
    # Assertions
    assert isinstance(result, pd.DataFrame)
    mock_save.assert_called_once()


@patch('eranest.core.process_era5')
def test_era5ify_geojson(mock_process, sample_geojson_file):
    mock_process.return_value = pd.DataFrame({"test": [1, 2, 3]})
    
    result = era5ify_geojson(
        request_id="test",
        variables=["t2m"],
        start_date="2020-01-01",
        end_date="2020-01-02",
        json_file=sample_geojson_file
    )
    
    assert isinstance(result, pd.DataFrame)
    mock_process.assert_called_once()


@patch('eranest.core.process_era5')
def test_era5ify_bbox(mock_process):
    mock_process.return_value = pd.DataFrame({"test": [1, 2, 3]})
    
    result = era5ify_bbox(
        request_id="test",
        variables=["t2m"],
        start_date="2020-01-01",
        end_date="2020-01-02",
        north=38.0,
        south=37.5,
        east=-122.0,
        west=-122.5
    )
    
    assert isinstance(result, pd.DataFrame)
    mock_process.assert_called_once()


@patch('eranest.core.process_era5')
def test_era5ify_point(mock_process):
    mock_process.return_value = pd.DataFrame({"test": [1, 2, 3]})
    
    result = era5ify_point(
        request_id="test",
        variables=["t2m"],
        start_date="2020-01-01",
        end_date="2020-01-02",
        latitude=37.75,
        longitude=-122.25
    )
    
    assert isinstance(result, pd.DataFrame)
    mock_process.assert_called_once()

def test_adjust_sum_variables_monthly():
    """Test monthly adjustment of sum variables"""
    # Create test DataFrame
    test_df = pd.DataFrame({
        'year': [2020, 2020, 2021],  # 2020 is a leap year
        'month': [1, 2, 2],          # January, February (leap), February (non-leap)
        'tp': [10, 15, 20],          # Sum variable (precipitation)
        't2m': [280, 281, 282]       # Non-sum variable (temperature)
    })
    
    # Make a copy for comparison
    original_df = test_df.copy()
    
    # Call the function
    adjust_sum_variables(test_df, 'monthly')
    
    # Verify adjustments
    jan_days = monthrange(2020, 1)[1]  # 31 days
    feb_leap_days = monthrange(2020, 2)[1]  # 29 days (leap year)
    feb_normal_days = monthrange(2021, 2)[1]  # 28 days
    print(test_df)
    assert test_df['tp'][0] == original_df['tp'][0] * jan_days
    assert test_df['tp'][1] == original_df['tp'][1] * feb_leap_days
    assert test_df['tp'][2] == original_df['tp'][2] * feb_normal_days
    assert test_df['t2m'][0] == original_df['t2m'][0]  # Should remain unchanged
    assert 'days_in_month' not in test_df.columns  # Column should be removed

def test_adjust_sum_variables_yearly():
    """Test yearly adjustment of sum variables"""
    test_df = pd.DataFrame({
        'year': [2020, 2021],
        'month': [1, 1],
        'tp': [10, 15],
        'ssr': [100, 150]  # Another sum variable (solar radiation)
    })
    
    original_df = test_df.copy()
    
    adjust_sum_variables(test_df, 'yearly')
    
    # Verify yearly adjustment factor (30.4375 days/month average)
    assert test_df['tp'][0] == original_df['tp'][0] * 30.4375
    assert test_df['ssr'][0] == original_df['ssr'][0] * 30.4375
    assert test_df['month'][0] == original_df['month'][0]  # Month column unchanged

def test_adjust_sum_variables_no_sum_vars():
    """Test with DataFrame containing no sum variables"""
    test_df = pd.DataFrame({
        'year': [2020],
        'month': [1],
        't2m': [280]  # Not in SUM_VARS
    })
    
    original_df = test_df.copy()
    
    adjust_sum_variables(test_df, 'monthly')
    
    # DataFrame should remain unchanged
    pd.testing.assert_frame_equal(test_df, original_df)
