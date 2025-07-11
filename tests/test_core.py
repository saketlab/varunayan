import pytest
import datetime as dt
import pandas as pd
import xarray as xr
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
    validate_inputs
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

@patch('time.sleep')  # Mock sleep to avoid waiting
def test_download_with_retry_failure(mock_sleep, basic_params):
    def failing_download(**kwargs):
        raise Exception("Download failed")
    
    with pytest.raises(Exception):
        download_with_retry(failing_download, basic_params)
    
    # Should have tried to sleep between retries
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