import datetime as dt
import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from varunayan.cli import main, parse_flexible_date


class TestParseFlexibleDate:
    """Test the parse_flexible_date function"""

    def test_parse_yyyy_mm_dd_format(self):
        """Test parsing YYYY-MM-DD format"""
        result = parse_flexible_date("2023-01-15")
        expected = dt.datetime(2023, 1, 15)
        assert result == expected

    def test_parse_yyyy_m_d_format(self):
        """Test parsing YYYY-M-D format"""
        result = parse_flexible_date("2023-1-5")
        expected = dt.datetime(2023, 1, 5)
        assert result == expected

    def test_parse_mixed_format(self):
        """Test parsing mixed format YYYY-MM-D"""
        result = parse_flexible_date("2023-01-5")
        expected = dt.datetime(2023, 1, 5)
        assert result == expected

    def test_invalid_date_format(self):
        """Test that invalid date formats raise ValueError"""
        with pytest.raises(
            ValueError,
            match="Date '2023/01/15' must be in YYYY-MM-DD or YYYY-M-D format",
        ):
            parse_flexible_date("2023/01/15")

    def test_invalid_date_value(self):
        """Test that invalid date values raise ValueError"""
        with pytest.raises(ValueError):
            parse_flexible_date("2023-13-01")  # Invalid month


class TestCLIMain:
    """Test the main CLI function"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_df = MagicMock()

    @patch("varunayan.cli.era5ify_geojson")
    @patch("varunayan.cli.get_logger")
    def test_geojson_mode_success(self, mock_logger, mock_era5ify_geojson):
        """Test successful execution in geojson mode"""
        mock_era5ify_geojson.return_value = self.mock_df

        test_args = [
            "geojson",
            "--request-id",
            "test-123",
            "--variables",
            "temperature,humidity",
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-31",
            "--geojson",
            "test.geojson",
            "--dataset-type",
            "single",
            "--freq",
            "daily",
            "--res",
            "0.1",
        ]

        with patch("sys.argv", ["cli.py"] + test_args):
            main()

        mock_era5ify_geojson.assert_called_once_with(
            request_id="test-123",
            variables=["temperature", "humidity"],
            start_date="2023-01-01",
            end_date="2023-01-31",
            json_file="test.geojson",
            dataset_type="single",
            pressure_levels=[],
            frequency="daily",
            resolution=0.1,
        )

    @patch("varunayan.cli.era5ify_bbox")
    @patch("varunayan.cli.get_logger")
    def test_bbox_mode_success(self, mock_logger, mock_era5ify_bbox):
        """Test successful execution in bbox mode"""
        mock_era5ify_bbox.return_value = self.mock_df

        test_args = [
            "bbox",
            "--request-id",
            "test-456",
            "--variables",
            "wind_speed,pressure",
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-31",
            "--north",
            "40.0",
            "--south",
            "30.0",
            "--east",
            "-70.0",
            "--west",
            "-80.0",
            "--dataset-type",
            "pressure",
            "--pressure-levels",
            "1000,925,850",
            "--freq",
            "hourly",
        ]

        with patch("sys.argv", ["cli.py"] + test_args):
            main()

        mock_era5ify_bbox.assert_called_once_with(
            request_id="test-456",
            variables=["wind_speed", "pressure"],
            start_date="2023-01-01",
            end_date="2023-01-31",
            north=40.0,
            south=30.0,
            east=-70.0,
            west=-80.0,
            dataset_type="pressure",
            pressure_levels=["1000", "925", "850"],
            frequency="hourly",
            resolution=0.25,
        )

    @patch("varunayan.cli.era5ify_point")
    @patch("varunayan.cli.get_logger")
    def test_point_mode_success(self, mock_logger, mock_era5ify_point):
        """Test successful execution in point mode"""
        mock_era5ify_point.return_value = self.mock_df

        test_args = [
            "point",
            "--request-id",
            "test-789",
            "--variables",
            "temperature",
            "--start",
            "2023-1-1",
            "--end",
            "2023-1-31",
            "--lat",
            "35.5",
            "--lon",
            "-78.5",
            "--dataset-type",
            "single",
            "--freq",
            "monthly",
        ]

        with patch("sys.argv", ["cli.py"] + test_args):
            main()

        mock_era5ify_point.assert_called_once_with(
            request_id="test-789",
            variables=["temperature"],
            start_date="2023-1-1",
            end_date="2023-1-31",
            latitude=35.5,
            longitude=-78.5,
            dataset_type="single",
            pressure_levels=[],
            frequency="monthly",
        )

    @patch("varunayan.cli.logger")  # Patch the actual logger instance
    def test_invalid_date_format_error(self, mock_logger):
        test_args = [
            "geojson",
            "--request-id",
            "test-123",
            "--variables",
            "temperature",
            "--start",
            "2023/01/01",
            "--end",
            "2023-01-31",
            "--geojson",
            "test.geojson",
        ]

        with patch("sys.argv", ["cli.py"] + test_args):
            main()

        mock_logger.error.assert_called_with(
            "Error parsing dates: Date '2023/01/01' must be in "
            "YYYY-MM-DD or YYYY-M-D format"
        )

    @patch("varunayan.cli.era5ify_geojson")
    @patch("varunayan.cli.get_logger")
    def test_pressure_levels_parsing(self, mock_logger, mock_era5ify_geojson):
        """Test parsing of pressure levels"""
        mock_era5ify_geojson.return_value = self.mock_df

        test_args = [
            "geojson",
            "--request-id",
            "test-123",
            "--variables",
            "temperature",
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-31",
            "--geojson",
            "test.geojson",
            "--dataset-type",
            "pressure",
            "--pressure-levels",
            "1000, 925, 850, 500",  # With spaces
        ]

        with patch("sys.argv", ["cli.py"] + test_args):
            main()

        # Check that pressure levels were parsed correctly
        call_args = mock_era5ify_geojson.call_args[1]
        assert call_args["pressure_levels"] == ["1000", "925", "850", "500"]

    @patch("varunayan.cli.era5ify_geojson")
    @patch("varunayan.cli.get_logger")
    def test_empty_pressure_levels(self, mock_logger, mock_era5ify_geojson):
        """Test handling of empty pressure levels"""
        mock_era5ify_geojson.return_value = self.mock_df

        test_args = [
            "geojson",
            "--request-id",
            "test-123",
            "--variables",
            "temperature",
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-31",
            "--geojson",
            "test.geojson",
            "--pressure-levels",
            "",  # Empty string
        ]

        with patch("sys.argv", ["cli.py"] + test_args):
            main()

        # Check that empty pressure levels result in empty list
        call_args = mock_era5ify_geojson.call_args[1]
        assert call_args["pressure_levels"] == []

    @patch("varunayan.cli.era5ify_geojson")
    @patch("varunayan.cli.get_logger")
    def test_variable_parsing_with_spaces(self, mock_logger, mock_era5ify_geojson):
        """Test parsing of variables with spaces"""
        mock_era5ify_geojson.return_value = self.mock_df

        test_args = [
            "geojson",
            "--request-id",
            "test-123",
            "--variables",
            "temperature, humidity, wind_speed",  # With spaces
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-31",
            "--geojson",
            "test.geojson",
        ]

        with patch("sys.argv", ["cli.py"] + test_args):
            main()

        # Check that variables were parsed correctly
        call_args = mock_era5ify_geojson.call_args[1]
        assert call_args["variables"] == ["temperature", "humidity", "wind_speed"]

    @patch("varunayan.cli.era5ify_geojson")
    @patch("varunayan.cli.get_logger")
    def test_default_values(self, mock_logger, mock_era5ify_geojson):
        """Test that default values are used correctly"""
        mock_era5ify_geojson.return_value = self.mock_df

        test_args = [
            "geojson",
            "--request-id",
            "test-123",
            "--variables",
            "temperature",
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-31",
            "--geojson",
            "test.geojson",
            # No explicit dataset-type, freq, or res
        ]

        with patch("sys.argv", ["cli.py"] + test_args):
            main()

        call_args = mock_era5ify_geojson.call_args[1]
        assert call_args["dataset_type"] == "single"
        assert call_args["frequency"] == "hourly"
        assert call_args["resolution"] == 0.25

    def test_missing_required_arguments(self):
        """Test error handling for missing required arguments"""
        test_args = [
            "geojson",
            "--request-id",
            "test-123",
            # Missing variables, start, end, geojson
        ]

        with patch("sys.argv", ["cli.py"] + test_args):
            with pytest.raises(SystemExit):
                main()

    def test_invalid_dataset_type(self):
        """Test error handling for invalid dataset type"""
        test_args = [
            "geojson",
            "--request-id",
            "test-123",
            "--variables",
            "temperature",
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-31",
            "--geojson",
            "test.geojson",
            "--dataset-type",
            "invalid",
        ]

        with patch("sys.argv", ["cli.py"] + test_args):
            with pytest.raises(SystemExit):
                main()

    def test_invalid_frequency(self):
        """Test error handling for invalid frequency"""
        test_args = [
            "geojson",
            "--request-id",
            "test-123",
            "--variables",
            "temperature",
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-31",
            "--geojson",
            "test.geojson",
            "--freq",
            "invalid",
        ]

        with patch("sys.argv", ["cli.py"] + test_args):
            with pytest.raises(SystemExit):
                main()

    def test_no_mode_specified(self):
        """Test error handling when no mode is specified"""
        test_args = [
            "--request-id",
            "test-123",
            "--variables",
            "temperature",
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-31",
        ]

        with patch("sys.argv", ["cli.py"] + test_args):
            with pytest.raises(SystemExit):
                main()


class TestCLIIntegration:
    """Integration tests for the CLI"""

    @patch("varunayan.cli.era5ify_geojson")
    @patch("varunayan.cli.get_logger")
    def test_full_workflow_geojson(self, mock_logger, mock_era5ify_geojson):
        """Test a complete workflow with geojson mode"""
        # Create a simple mock DataFrame
        mock_df = pd.DataFrame(
            {
                "temperature": [20.1, 21.2, 22.3],
                "humidity": [45, 50, 55],
                "wind_speed": [3.2, 4.1, 5.0],
            }
        )
        mock_era5ify_geojson.return_value = mock_df

        test_args = [
            "geojson",
            "--request-id",
            "full-test-123",
            "--variables",
            "temperature,humidity,wind_speed",
            "--start",
            "2023-01-01",
            "--end",
            "2023-12-31",
            "--geojson",
            "/path/to/regions.geojson",
            "--dataset-type",
            "pressure",
            "--pressure-levels",
            "1000,925,850,700,500",
            "--freq",
            "daily",
            "--res",
            "0.1",
        ]

        with patch("sys.argv", ["cli.py"] + test_args):
            main()

        mock_era5ify_geojson.assert_called_once()
        call_args = mock_era5ify_geojson.call_args[1]

        assert call_args["request_id"] == "full-test-123"
        assert call_args["variables"] == ["temperature", "humidity", "wind_speed"]
        assert call_args["start_date"] == "2023-01-01"
        assert call_args["end_date"] == "2023-12-31"
        assert call_args["json_file"] == "/path/to/regions.geojson"
        assert call_args["dataset_type"] == "pressure"
        assert call_args["pressure_levels"] == ["1000", "925", "850", "700", "500"]
        assert call_args["frequency"] == "daily"
        assert call_args["resolution"] == 0.1


# Fixtures for testing
@pytest.fixture
def mock_df():
    """Mock DataFrame for testing"""
    return MagicMock()


@pytest.fixture
def sample_geojson_file_cli(tmp_path):
    """Create a sample GeoJSON file for testing"""
    geojson_content = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-74.0059, 40.7128]},
                "properties": {"name": "New York City"},
            }
        ],
    }

    geojson_file = tmp_path / "test.geojson"
    with open(geojson_file, "w") as f:
        json.dump(geojson_content, f)

    return str(geojson_file)


# Parametrized tests
@pytest.mark.parametrize(
    "mode,extra_args",
    [
        ("geojson", ["--geojson", "test.geojson"]),
        ("bbox", ["--north", "40", "--south", "30", "--east", "-70", "--west", "-80"]),
        ("point", ["--lat", "35.5", "--lon", "-78.5"]),
    ],
)
@patch("varunayan.cli.era5ify_geojson")
@patch("varunayan.cli.era5ify_bbox")
@patch("varunayan.cli.era5ify_point")
@patch("varunayan.cli.get_logger")
def test_all_modes(
    mock_logger,
    mock_era5ify_point,
    mock_era5ify_bbox,
    mock_era5ify_geojson,
    mode,
    extra_args,
):
    """Parametrized test for all modes"""
    # Mock all functions to return a mock dataframe
    mock_df = MagicMock()
    mock_era5ify_geojson.return_value = mock_df
    mock_era5ify_bbox.return_value = mock_df
    mock_era5ify_point.return_value = mock_df

    base_args = [
        mode,
        "--request-id",
        "test-123",
        "--variables",
        "temperature",
        "--start",
        "2023-01-01",
        "--end",
        "2023-01-31",
    ]

    test_args = base_args + extra_args

    with patch("sys.argv", ["cli.py"] + test_args):
        main()

    # Verify the correct function was called based on mode
    if mode == "geojson":
        mock_era5ify_geojson.assert_called_once()
    elif mode == "bbox":
        mock_era5ify_bbox.assert_called_once()
    elif mode == "point":
        mock_era5ify_point.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
