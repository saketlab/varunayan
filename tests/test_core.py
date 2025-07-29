import datetime as dt
import sys
import unittest.mock as mock
from calendar import monthrange
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from varunayan.core import (
    ProcessingParams,
    adjust_sum_variables,
    aggregate_and_save,
    cleanup_temp_files,
    download_with_retry,
    era5ify_bbox,
    era5ify_geojson,
    era5ify_point,
    load_and_validate_geojson,
    parse_date,
    print_bounding_box,
    print_processing_header,
    print_processing_strategy,
    process_era5,
    process_era5_data,
    process_time_chunks,
    validate_inputs,
)

# Block ALL network calls
sys.modules["cdsapi"] = MagicMock()
sys.modules["urllib.request"] = MagicMock()
sys.modules["requests"] = MagicMock()


def test_processing_params_initialization(basic_params: ProcessingParams):
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


def test_validate_inputs(basic_params: ProcessingParams):
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
            west=basic_params.west,
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
            west=basic_params.west,
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
            dataset_type="pressure",
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
            geojson_file="yay.json",
        )
        validate_inputs(invalid_params)


def test_download_with_retry_success(basic_params: ProcessingParams, tmp_path: Path):
    # Setup test file
    test_file = tmp_path / "test_request.zip"
    test_file.touch()

    # Create a mock download function that returns the test file path
    def mock_download_func(**kwargs: Dict[str, Any]):
        return str(test_file)

    # Test the download with retry
    result = download_with_retry(mock_download_func, basic_params)

    # Verification
    assert result == str(test_file)


def test_download_with_retry_success_mo(
    basic_params_mo: ProcessingParams, tmp_path: Path
):
    # Setup test file
    test_file = tmp_path / "test_request.zip"
    test_file.touch()

    # Create a mock download function that returns the test file path
    def mock_download_func(**kwargs: Dict[str, Any]):
        return str(test_file)

    # Test the download with retry
    result = download_with_retry(mock_download_func, basic_params_mo)

    # Verification
    assert result == str(test_file)


def test_download_with_retry_pressure_levels_with_mock(
    pressure_params: ProcessingParams, tmp_path: Path
):
    # Setup test file
    test_file = tmp_path / "test_request.zip"
    test_file.touch()

    # Option 1: If core.py imports like:
    # from varunayan.download import download_era5_pressure_lvl
    # Then patch in core where it's imported:
    with mock.patch(
        "varunayan.core.download_era5_pressure_lvl", return_value=str(test_file)
    ) as mock_download:
        from varunayan.core import download_era5_pressure_lvl as download_func

        result = download_with_retry(download_func, pressure_params)

    # Verify the mock was called with pressure_levels
    mock_download.assert_called_once()
    call_args = mock_download.call_args[1]
    print("Call args:", call_args)
    assert "pressure_levels" in call_args, f"pressure_levels not found in {call_args}"
    assert call_args["pressure_levels"] == pressure_params.pressure_levels

    assert result == str(test_file)


@patch("time.sleep")  # Mock sleep to avoid waiting
def test_download_with_retry_failure(
    mock_sleep: MagicMock, basic_params: ProcessingParams
):
    def failing_download(**kwargs: Dict[str, Any]):
        raise Exception("Download failed")

    with pytest.raises(Exception):
        download_with_retry(failing_download, basic_params)

    assert mock_sleep.call_count > 0


@patch("varunayan.core.process_era5_data")
def test_process_time_chunks_no_chunking(
    mock_process: MagicMock, basic_params: ProcessingParams
):
    mock_process.return_value = pd.DataFrame({"test": [1, 2, 3]})

    # Create a mock download function
    def mock_proc_func(
        params: ProcessingParams,
        chunk_num: Optional[int] = None,
        total_chunks: Optional[int] = None,
    ):
        return mock_process(params)

    def mock_down_func():
        return None

    result = process_time_chunks(basic_params, mock_down_func, mock_proc_func)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3


@patch("varunayan.core.process_era5_data")
def test_process_time_chunks_no_chunking_mo(
    mock_process: MagicMock, basic_params_mo: ProcessingParams
):
    mock_process.return_value = pd.DataFrame({"test": [1, 2, 3]})

    # Create a mock download function
    def mock_proc_func(
        params: ProcessingParams,
        chunk_num: Optional[int] = None,
        total_chunks: Optional[int] = None,
    ):
        return mock_process(params)

    def mock_down_func():
        return None

    result = process_time_chunks(basic_params_mo, mock_down_func, mock_proc_func)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3


@patch("time.sleep")
@patch("varunayan.core.process_era5_data")
def test_process_time_chunks_with_chunking(
    mock_process: MagicMock, basic_params: ProcessingParams
):
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
        west=basic_params.west,
    )

    # Create a mock download function
    def mock_proc_func(
        params: ProcessingParams,
        chunk_num: Optional[int] = None,
        total_chunks: Optional[int] = None,
    ):
        return mock_process(params)

    def mock_down_func():
        return None

    result = process_time_chunks(chunk_params, mock_down_func, mock_proc_func)
    assert isinstance(result, pd.DataFrame)


@patch("time.sleep")
@patch("varunayan.core.process_era5_data")
def test_process_time_chunks_with_chunking_mo_pr(
    mock_process: MagicMock, basic_params: ProcessingParams
):
    mock_process.return_value = pd.DataFrame({"test": [1, 2, 3]})

    # Create params that would require chunking (>14 days)
    chunk_params = ProcessingParams(
        request_id=basic_params.request_id,
        variables=basic_params.variables,
        start_date=dt.datetime(1960, 1, 1),
        end_date=dt.datetime(2020, 2, 15),
        frequency="monthly",
        resolution=basic_params.resolution,
        north=basic_params.north,
        south=basic_params.south,
        east=basic_params.east,
        west=basic_params.west,
        pressure_levels=["1000"],
    )

    # Create a mock download function
    def mock_proc_func(
        params: ProcessingParams,
        chunk_num: Optional[int] = None,
        total_chunks: Optional[int] = None,
    ):
        return mock_process(params)

    def mock_down_func():
        return None

    result = process_time_chunks(chunk_params, mock_down_func, mock_proc_func)
    assert isinstance(result, pd.DataFrame)


@patch("varunayan.core.save_results")
@patch("varunayan.core.aggregate_by_frequency")
def test_aggregate_and_save(
    mock_agg: MagicMock,
    mock_save: MagicMock,
    basic_params: ProcessingParams,
    temp_dir: Path,
    save_raw: bool = True,
):
    test_df = pd.DataFrame(
        {
            "valid_time": pd.to_datetime(["2020-01-01", "2020-01-02"]),  # type: ignore
            "latitude": [37.75, 37.75],
            "longitude": [-122.25, -122.25],
            "t2m": [280, 281],
            "tp": [0, 0.1],
        }
    )

    # Mock aggregation to return the same dataframe
    mock_agg.return_value = (test_df, pd.DataFrame())

    result = aggregate_and_save(basic_params, test_df, save_raw)

    # Assertions
    assert isinstance(result, pd.DataFrame)
    mock_save.assert_called_once()


@patch("varunayan.core.process_era5")
def test_era5ify_geojson(mock_process: MagicMock, sample_geojson_file: str):
    mock_process.return_value = pd.DataFrame({"test": [1, 2, 3]})

    result = era5ify_geojson(
        request_id="test",
        variables=["t2m"],
        start_date="2020-01-01",
        end_date="2020-01-02",
        json_file=sample_geojson_file,
    )

    assert isinstance(result, pd.DataFrame)
    mock_process.assert_called_once()


@patch("varunayan.core.process_era5")
def test_era5ify_bbox(mock_process: MagicMock):
    mock_process.return_value = pd.DataFrame({"test": [1, 2, 3]})

    result = era5ify_bbox(
        request_id="test",
        variables=["t2m"],
        start_date="2020-01-01",
        end_date="2020-01-02",
        north=38.0,
        south=37.5,
        east=-122.0,
        west=-122.5,
    )

    assert isinstance(result, pd.DataFrame)
    mock_process.assert_called_once()


@patch("varunayan.core.process_era5")
def test_era5ify_point(mock_process: MagicMock):
    mock_process.return_value = pd.DataFrame({"test": [1, 2, 3]})

    result = era5ify_point(
        request_id="test",
        variables=["t2m"],
        start_date="2020-01-01",
        end_date="2020-01-02",
        latitude=37.75,
        longitude=-122.25,
    )

    assert isinstance(result, pd.DataFrame)
    mock_process.assert_called_once()


def test_adjust_sum_variables_monthly():
    """Test monthly adjustment of sum variables"""
    # Create test DataFrame
    test_df = pd.DataFrame(
        {
            "year": [2020, 2020, 2021],  # 2020 is a leap year
            "month": [1, 2, 2],  # Jan, Feb (leap), Feb (non-leap)
            "tp": [10, 15, 20],  # Sum variable (precipitation)
            "t2m": [280, 281, 282],  # Non-sum variable (temperature)
        }
    )

    # Make a copy for comparison
    original_df = test_df.copy()

    # Call the function
    adjust_sum_variables(test_df, "monthly")

    # Verify adjustments
    jan_days = monthrange(2020, 1)[1]  # 31 days
    feb_leap_days = monthrange(2020, 2)[1]  # 29 days (leap year)
    feb_normal_days = monthrange(2021, 2)[1]  # 28 days
    print(test_df)
    assert test_df["tp"][0] == original_df["tp"][0] * jan_days
    assert test_df["tp"][1] == (original_df["tp"][1] * feb_leap_days)
    assert test_df["tp"][2] == original_df["tp"][2] * feb_normal_days
    # Should remain unchanged
    assert test_df["t2m"][0] == original_df["t2m"][0]
    assert "days_in_month" not in test_df.columns  # Column should be removed


def test_adjust_sum_variables_yearly():
    """Test yearly adjustment of sum variables"""
    test_df = pd.DataFrame(
        {
            "year": [2020, 2021],
            "month": [1, 1],
            "tp": [10, 15],
            "ssr": [100, 150],  # Another sum variable (solar radiation)
        }
    )

    original_df = test_df.copy()

    adjust_sum_variables(test_df, "yearly")

    # Verify yearly adjustment factor (30.4375 days/month average)
    assert test_df["tp"][0] == original_df["tp"][0] * 30.4375
    assert test_df["ssr"][0] == (original_df["ssr"][0] * 30.4375)
    # Month column unchanged
    assert test_df["month"][0] == original_df["month"][0]


def test_adjust_sum_variables_no_sum_vars():
    """Test with DataFrame containing no sum variables"""
    test_df = pd.DataFrame(
        {"year": [2020], "month": [1], "t2m": [280]}  # Not in SUM_VARS
    )

    original_df = test_df.copy()

    adjust_sum_variables(test_df, "monthly")

    # DataFrame should remain unchanged
    pd.testing.assert_frame_equal(test_df, original_df)


def test_load_and_validate_geojson():
    """Test loading and validating a GeoJSON file without file system operations"""
    # Mock the file reading and JSON loading
    mock_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
            }
        ],
    }

    with patch(
        "varunayan.core.load_json_with_encoding", return_value=mock_geojson
    ), patch("varunayan.core.is_valid_geojson", return_value=True), patch(
        "varunayan.core.logger"
    ) as mock_logger:

        # We don't need a real file path since we're mocking everything
        result = load_and_validate_geojson("dummy_path.json")

        assert result == mock_geojson
        mock_logger.debug.assert_called_with(
            "\x1b[0;32m✓ GeoJSON loaded successfully\x1b[0m"
        )


def test_print_bounding_box():
    """Test printing bounding box information"""
    params = ProcessingParams(
        request_id="test",
        variables=["t2m"],
        start_date=dt.datetime(2020, 1, 1),
        end_date=dt.datetime(2020, 1, 2),
        north=38.0,
        south=37.5,
        east=-122.0,
        west=-122.5,
    )

    with patch("varunayan.core.logger") as mock_logger:
        print_bounding_box(params)

        mock_logger.info.assert_any_call("  North: 38.0000°")
        mock_logger.info.assert_any_call("  South: 37.5000°")
        mock_logger.info.assert_any_call("  East:  -122.0000°")
        mock_logger.info.assert_any_call("  West:  -122.5000°")


def test_print_processing_strategy_monthly():
    """Test printing processing strategy for monthly data"""
    params = ProcessingParams(
        request_id="test",
        variables=["t2m"],
        start_date=dt.datetime(2020, 1, 1),
        end_date=dt.datetime(2020, 12, 31),
        frequency="monthly",
    )

    with patch("varunayan.core.logger") as mock_logger:
        print_processing_strategy(params)

        mock_logger.debug.assert_any_call("Using monthly dataset: True")
        mock_logger.debug.assert_any_call("Total months to process: 12")


def test_print_processing_strategy_daily():
    """Test printing processing strategy for daily data"""
    params = ProcessingParams(
        request_id="test",
        variables=["t2m"],
        start_date=dt.datetime(2020, 1, 1),
        end_date=dt.datetime(2020, 1, 14),
        frequency="daily",
    )

    with patch("varunayan.core.logger") as mock_logger:
        print_processing_strategy(params)

        mock_logger.debug.assert_any_call("Using monthly dataset: False")
        mock_logger.debug.assert_any_call("Total days to process: 14")


@patch("os.path.exists", return_value=True)
def test_validate_inputs_with_geojson(mock_exists: MagicMock):
    """Test input validation with GeoJSON file"""
    params = ProcessingParams(
        request_id="test",
        variables=["t2m"],
        start_date=dt.datetime(2020, 1, 1),
        end_date=dt.datetime(2020, 1, 2),
        geojson_file="test.json",
    )

    # Should not raise any exceptions
    validate_inputs(params)


def test_validate_inputs_pressure_levels():
    """Test input validation for pressure level data"""
    params = ProcessingParams(
        request_id="test",
        variables=["t"],
        start_date=dt.datetime(2020, 1, 1),
        end_date=dt.datetime(2020, 1, 2),
        dataset_type="pressure",
        pressure_levels=["500", "850"],
    )

    # Should not raise any exceptions
    validate_inputs(params)


@patch("os.path.exists", return_value=True)
@patch("os.remove")
@patch("shutil.rmtree")
@patch("glob.glob")
def test_cleanup_temp_files(
    mock_glob: MagicMock,
    mock_rmtree: MagicMock,
    mock_remove: MagicMock,
    mock_exists: MagicMock,
):
    """Test cleanup of temporary files"""

    # Mock glob to return files for both patterns
    def mock_glob_side_effect(pattern: str) -> Optional[List[str]]:
        if "*test123*.zip" in pattern:
            return ["/tmp/test123.zip"]
        elif "*test123*.nc" in pattern:
            return ["/tmp/test123.nc"]
        else:
            return []

    mock_glob.side_effect = mock_glob_side_effect

    cleanup_temp_files("test123", "/tmp/test123.json")

    # Check that remove was called for the temp_geojson_file
    mock_remove.assert_any_call("/tmp/test123.json")
    # Check that remove was called for the glob files
    mock_remove.assert_any_call("/tmp/test123.zip")
    mock_remove.assert_any_call("/tmp/test123.nc")

    # The function calls glob twice (once for *.zip, once for *.nc)
    # So we expect 3 remove calls: temp_geojson_file + zip file + nc file
    assert mock_remove.call_count == 3


@patch("varunayan.core.aggregate_and_save")
@patch("varunayan.core.print_bounding_box")
@patch("varunayan.core.print_processing_footer")
@patch("varunayan.core.print_processing_header")
@patch("varunayan.core.validate_inputs")
@patch("varunayan.core.process_time_chunks")
def test_process_era5(
    mock_print_bbox: MagicMock,
    mock_footer: MagicMock,
    mock_header: MagicMock,
    mock_validate: MagicMock,
    mock_process: MagicMock,
    mock_agg: MagicMock,
):
    """Test main process_era5 function with mocked dependencies"""
    # Setup mock return values
    mock_df = pd.DataFrame({"test": [1, 2, 3]})
    mock_agg.return_value = mock_df

    # Create test params
    params = ProcessingParams(
        request_id="test",
        variables=["t2m"],
        start_date=dt.datetime(2020, 1, 1),
        end_date=dt.datetime(2020, 1, 2),
    )
    save_raw = True

    # Call the function
    result = process_era5(params, save_raw)

    # Verify
    print(result)
    assert isinstance(result, pd.DataFrame)
    mock_validate.assert_called_once()
    mock_header.assert_called_once()
    mock_process.assert_called_once()
    mock_footer.assert_called_once()


@patch("varunayan.core.process_era5")
def test_era5ify_point_edge_cases(mock_process: MagicMock):
    """Test era5ify_point with edge case coordinates"""
    mock_process.return_value = pd.DataFrame({"test": [1, 2, 3]})

    # Test near North Pole
    result = era5ify_point(
        request_id="test",
        variables=["t2m"],
        start_date="2020-01-01",
        end_date="2020-01-02",
        latitude=89.9,
        longitude=0,
    )
    assert isinstance(result, pd.DataFrame)

    # Test near antimeridian
    result = era5ify_point(
        request_id="test",
        variables=["t2m"],
        start_date="2020-01-01",
        end_date="2020-01-02",
        latitude=0,
        longitude=179.9,
    )
    assert isinstance(result, pd.DataFrame)


def test_adjust_sum_variables_edge_cases():
    """Test sum variable adjustment with edge cases"""
    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    adjust_sum_variables(empty_df, "monthly")  # Should not raise any errors

    # Test with DataFrame containing only sum variables
    sum_df = pd.DataFrame({"year": [2020], "month": [1], "tp": [10], "ssr": [100]})
    original_sum_df = sum_df.copy()
    adjust_sum_variables(sum_df, "monthly")
    assert not sum_df.equals(original_sum_df)  # Values should have changed


def test_print_processing_header_pressure():
    """Test header printing with pressure level data"""
    params = ProcessingParams(
        request_id="test_pressure",
        variables=["t"],
        start_date=dt.datetime(2020, 1, 1),
        end_date=dt.datetime(2020, 1, 2),
        pressure_levels=["500", "850"],
        geojson_file="jfile.json",
    )

    with patch("varunayan.core.always_logger") as mock_logger:
        print_processing_header(params)
        mock_logger.info.assert_any_call("Pressure Levels: ['500', '850']")


@patch("varunayan.core.logger")
@patch("varunayan.core.filter_netcdf_by_shapefile")
@patch("varunayan.core.extract_download")
@patch("varunayan.core.download_with_retry")
@patch("xarray.open_dataset")
def test_process_era5_data_single_level_success(
    mock_open_dataset: MagicMock,
    mock_download: MagicMock,
    mock_extract: MagicMock,
    mock_filter: MagicMock,
    mock_logger: MagicMock,
    basic_params: ProcessingParams,
):
    """Test successful processing of single level data"""
    # Setup mock data
    mock_nc_file = "/tmp/test_data.nc"
    mock_download.return_value = "/tmp/test_request.zip"
    mock_extract.return_value = [mock_nc_file]

    # Create mock xarray dataset
    mock_ds = xr.Dataset(
        {
            "t2m": (["valid_time", "latitude", "longitude"], np.random.rand(24, 2, 2)),
            "tp": (["valid_time", "latitude", "longitude"], np.random.rand(24, 2, 2)),
        },
        coords={
            "valid_time": pd.date_range("2020-01-01", periods=24, freq="h"),
            "latitude": [37.5, 38.0],
            "longitude": [-122.5, -122.0],
        },
    )

    # Convert to expected DataFrame format
    # expected_df = mock_ds.to_dataframe().reset_index()  # Unused variable

    mock_open_dataset.return_value = mock_ds

    # Call the function
    result = process_era5_data(basic_params)

    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert "valid_time" in result.columns
    assert "latitude" in result.columns
    assert "longitude" in result.columns

    # Verify function calls
    mock_download.assert_called_once()
    mock_extract.assert_called_once_with("/tmp/test_request.zip")
    mock_open_dataset.assert_called_once_with(mock_nc_file)
    mock_logger.info.assert_called()


@patch("varunayan.core.logger")
@patch("varunayan.core.filter_netcdf_by_shapefile")
@patch("varunayan.core.extract_download")
@patch("varunayan.core.download_with_retry")
@patch("xarray.open_dataset")
def test_process_era5_data_pressure_level_success(
    mock_open_dataset: MagicMock,
    mock_download: MagicMock,
    mock_extract: MagicMock,
    mock_filter: MagicMock,
    mock_logger: MagicMock,
    pressure_params: ProcessingParams,
):
    """Test successful processing of pressure level data"""
    # Setup mock data
    mock_nc_file = "/tmp/test_pressure_data.nc"
    mock_download.return_value = "/tmp/test_request.zip"
    mock_extract.return_value = [mock_nc_file]

    # Create mock xarray dataset with pressure levels
    mock_ds = xr.Dataset(
        {
            "t": (
                ["valid_time", "pressure_level", "latitude", "longitude"],
                np.random.rand(24, 2, 2, 2),
            ),
            "u": (
                ["valid_time", "pressure_level", "latitude", "longitude"],
                np.random.rand(24, 2, 2, 2),
            ),
        },
        coords={
            "valid_time": pd.date_range("2020-01-01", periods=24, freq="h"),
            "pressure_level": [500, 850],
            "latitude": [37.5, 38.0],
            "longitude": [-122.5, -122.0],
        },
    )

    mock_open_dataset.return_value = mock_ds

    # Call the function
    result = process_era5_data(pressure_params)

    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert "pressure_level" in result.columns

    # Verify download function selection (should use pressure level downloader)
    mock_download.assert_called_once()
    call_args = mock_download.call_args
    # The first argument should be the pressure level download function
    assert "pressure_lvl" in str(call_args[0][0])


@patch("varunayan.core.logger")
@patch("varunayan.core.filter_netcdf_by_shapefile")
@patch("varunayan.core.extract_download")
@patch("varunayan.core.download_with_retry")
@patch("xarray.open_dataset")
def test_process_era5_data_with_geojson_filtering(
    mock_open_dataset: MagicMock,
    mock_download: MagicMock,
    mock_extract: MagicMock,
    mock_filter: MagicMock,
    mock_logger: MagicMock,
    basic_params: ProcessingParams,
):
    """Test processing with GeoJSON filtering"""
    # Setup params with geojson_data
    basic_params.geojson_data = {"type": "FeatureCollection", "features": []}

    # Setup mock data
    mock_nc_file = "/tmp/test_data.nc"
    mock_download.return_value = "/tmp/test_request.zip"
    mock_extract.return_value = [mock_nc_file]

    # Create mock dataset
    mock_ds = xr.Dataset(
        {"t2m": (["valid_time", "latitude", "longitude"], np.random.rand(24, 2, 2))},
        coords={
            "valid_time": pd.date_range("2020-01-01", periods=24, freq="h"),
            "latitude": [37.5, 38.0],
            "longitude": [-122.5, -122.0],
        },
    )

    # Mock filtered DataFrame
    filtered_df = pd.DataFrame(
        {
            "valid_time": pd.date_range("2020-01-01", periods=10, freq="h"),
            "latitude": [37.75] * 10,
            "longitude": [-122.25] * 10,
            "t2m": np.random.rand(10),
        }
    )

    mock_open_dataset.return_value = mock_ds
    mock_filter.return_value = filtered_df

    # Call the function
    result = process_era5_data(basic_params)

    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 10  # Should match filtered data
    mock_filter.assert_called_once_with(mock_ds, basic_params.geojson_data)


@patch("varunayan.core.logger")
@patch("varunayan.core.extract_download")
@patch("varunayan.core.download_with_retry")
@patch("xarray.open_dataset")
def test_process_era5_data_multiple_files(
    mock_open_dataset: MagicMock,
    mock_download: MagicMock,
    mock_extract: MagicMock,
    mock_logger: MagicMock,
    basic_params: ProcessingParams,
):
    """Test processing multiple NetCDF files"""
    # Setup mock data
    mock_nc_files = ["/tmp/file1.nc", "/tmp/file2.nc"]
    mock_download.return_value = "/tmp/test_request.zip"
    mock_extract.return_value = mock_nc_files

    # Create mock datasets
    mock_ds1 = xr.Dataset(
        {"t2m": (["valid_time", "latitude", "longitude"], np.random.rand(12, 2, 2))},
        coords={
            "valid_time": pd.date_range("2020-01-01", periods=12, freq="h"),
            "latitude": [37.5, 38.0],
            "longitude": [-122.5, -122.0],
        },
    )

    mock_ds2 = xr.Dataset(
        {"tp": (["valid_time", "latitude", "longitude"], np.random.rand(12, 2, 2))},
        coords={
            "valid_time": pd.date_range("2020-01-01", periods=12, freq="h"),
            "latitude": [37.5, 38.0],
            "longitude": [-122.5, -122.0],
        },
    )

    mock_open_dataset.side_effect = [mock_ds1, mock_ds2]

    # Call the function
    result = process_era5_data(basic_params)

    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert "t2m" in result.columns or "tp" in result.columns

    # Verify both files were processed
    assert mock_open_dataset.call_count == 2


@patch("varunayan.core.logger")
@patch("varunayan.core.extract_download")
@patch("varunayan.core.download_with_retry")
@patch("xarray.open_dataset")
def test_process_era5_data_with_duplicates(
    mock_open_dataset: MagicMock,
    mock_download: MagicMock,
    mock_extract: MagicMock,
    mock_logger: MagicMock,
    basic_params: ProcessingParams,
):
    """Test duplicate removal functionality"""
    # Setup mock data
    mock_nc_file = "/tmp/test_data.nc"
    mock_download.return_value = "/tmp/test_request.zip"
    mock_extract.return_value = [mock_nc_file]

    # Create dataset with duplicate entries
    time_coords = pd.date_range("2020-01-01", periods=2, freq="h")
    lat_coords = [37.5, 37.5]  # Duplicate latitude
    lon_coords = [-122.5, -122.5]  # Duplicate longitude

    mock_ds = xr.Dataset(
        {"t2m": (["valid_time", "latitude", "longitude"], np.random.rand(2, 2, 2))},
        coords={
            "valid_time": time_coords,
            "latitude": lat_coords,
            "longitude": lon_coords,
        },
    )

    mock_open_dataset.return_value = mock_ds

    # Call the function
    result = process_era5_data(basic_params)

    # Should still return DataFrame even with duplicates
    assert isinstance(result, pd.DataFrame)


@patch("varunayan.core.logger")
@patch("varunayan.core.extract_download")
@patch("varunayan.core.download_with_retry")
def test_process_era5_data_no_valid_files(
    mock_download: MagicMock,
    mock_extract: MagicMock,
    mock_logger: MagicMock,
    basic_params: ProcessingParams,
):
    """Test handling of no valid NetCDF files"""
    # Setup mock data with no .nc files
    mock_download.return_value = "/tmp/test_request.zip"
    mock_extract.return_value = ["file1.txt", "file2.dat"]  # No .nc files

    # Should raise ValueError
    with pytest.raises(ValueError, match="No valid datasets were processed"):
        process_era5_data(basic_params)


@patch("varunayan.core.logger")
@patch("varunayan.core.extract_download")
@patch("varunayan.core.download_with_retry")
@patch("xarray.open_dataset")
def test_process_era5_data_file_processing_error(
    mock_open_dataset: MagicMock,
    mock_download: MagicMock,
    mock_extract: MagicMock,
    mock_logger: MagicMock,
    basic_params: ProcessingParams,
):
    """Test handling of file processing errors"""
    # Setup mock data
    mock_nc_files = ["/tmp/good_file.nc", "/tmp/bad_file.nc"]
    mock_download.return_value = "/tmp/test_request.zip"
    mock_extract.return_value = mock_nc_files

    # Create one good dataset and one that raises an error
    mock_ds = xr.Dataset(
        {"t2m": (["valid_time", "latitude", "longitude"], np.random.rand(24, 2, 2))},
        coords={
            "valid_time": pd.date_range("2020-01-01", periods=24, freq="h"),
            "latitude": [37.5, 38.0],
            "longitude": [-122.5, -122.0],
        },
    )

    mock_open_dataset.side_effect = [mock_ds, Exception("File corrupted")]

    # Call the function - should process the good file and log error for bad file
    result = process_era5_data(basic_params)

    # Should still return DataFrame from the good file
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0

    # Should log error for the bad file
    mock_logger.error.assert_called()


@patch("varunayan.core.logger")
@patch("varunayan.core.extract_download")
@patch("varunayan.core.download_with_retry")
@patch("xarray.open_dataset")
def test_process_era5_data_with_chunk_info(
    mock_open_dataset: MagicMock,
    mock_download: MagicMock,
    mock_extract: MagicMock,
    mock_logger: MagicMock,
    basic_params: ProcessingParams,
):
    """Test processing with chunk information"""
    # Setup mock data
    mock_nc_file = "/tmp/test_data.nc"
    mock_download.return_value = "/tmp/test_request_chunk1.zip"
    mock_extract.return_value = [mock_nc_file]

    # Create mock dataset
    mock_ds = xr.Dataset(
        {"t2m": (["valid_time", "latitude", "longitude"], np.random.rand(24, 2, 2))},
        coords={
            "valid_time": pd.date_range("2020-01-01", periods=24, freq="h"),
            "latitude": [37.5, 38.0],
            "longitude": [-122.5, -122.0],
        },
    )

    mock_open_dataset.return_value = mock_ds

    # Call the function with chunk info
    chunk_info = (1, 3)  # Chunk 1 of 3
    result = process_era5_data(basic_params, chunk_info)

    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0

    # Verify that chunk ID was used in download
    mock_download.assert_called_once()
    call_args = mock_download.call_args
    # The chunk_id should be passed as the third argument
    assert "chunk1" in str(call_args)


@patch("varunayan.core.logger")
@patch("varunayan.core.extract_download")
@patch("varunayan.core.download_with_retry")
@patch("xarray.open_dataset")
def test_process_era5_data_all_files_fail(
    mock_open_dataset: MagicMock,
    mock_download: MagicMock,
    mock_extract: MagicMock,
    mock_logger: MagicMock,
    basic_params: ProcessingParams,
):
    """Test when all files fail to process"""
    # Setup mock data
    mock_nc_files = ["/tmp/file1.nc", "/tmp/file2.nc"]
    mock_download.return_value = "/tmp/test_request.zip"
    mock_extract.return_value = mock_nc_files

    # Make all files fail to process
    mock_open_dataset.side_effect = Exception("All files corrupted")

    # Should raise ValueError
    with pytest.raises(ValueError, match="No valid datasets were processed"):
        process_era5_data(basic_params)
