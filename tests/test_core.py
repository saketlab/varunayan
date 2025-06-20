#!/usr/bin/env python3
"""
Test suite for the modern eranest package.

This test suite validates the new optimized API and ensures
all modern functionality works correctly.
"""

import datetime as dt
from unittest.mock import MagicMock, patch

import pytest

# Import the modern eranest API
import eranest
from eranest.constants import AURORA_PRESSURE_LEVELS, DEFAULT_SURFACE_VARIABLES
from eranest.exceptions import DataDownloadError, ValidationError


class TestModernAPI:
    """Test the modern eranest API functions."""

    def test_package_metadata(self):
        """Test package metadata is accessible."""
        assert hasattr(eranest, "__version__")
        assert hasattr(eranest, "__author__")
        assert eranest.__version__ == "1.0.0"

    def test_main_functions_available(self):
        """Test that main API functions are available."""
        expected_functions = [
            "download_surface_data",
            "download_atmospheric_data",
            "download_static_data",
            "process_netcdf_dataset",
            "filter_by_geometry",
            "create_aurora_batch",
            "validate_coordinates",
            "extract_bounding_box",
        ]

        for func_name in expected_functions:
            assert hasattr(eranest, func_name), f"Missing function: {func_name}"
            assert callable(getattr(eranest, func_name)), f"Not callable: {func_name}"

    def test_constants_available(self):
        """Test that constants are accessible."""
        assert hasattr(eranest, "AURORA_PRESSURE_LEVELS")
        assert hasattr(eranest, "DEFAULT_SURFACE_VARIABLES")
        assert hasattr(eranest, "DataFrequency")

        assert len(AURORA_PRESSURE_LEVELS) > 0
        assert len(DEFAULT_SURFACE_VARIABLES) > 0

    def test_coordinate_validation(self):
        """Test coordinate validation functions."""
        # Valid coordinates
        assert eranest.validate_coordinates(25.0, 75.0) == True
        assert eranest.validate_coordinates(0.0, 0.0) == True
        assert eranest.validate_coordinates(90.0, 180.0) == True

        # Invalid coordinates in non-strict mode
        assert eranest.validate_coordinates(95.0, 75.0, strict=False) == False
        assert eranest.validate_coordinates(25.0, 185.0, strict=False) == False

        # Invalid coordinates in strict mode should raise exception
        with pytest.raises(ValidationError):
            eranest.validate_coordinates(95.0, 75.0, strict=True)

    def test_data_frequency_enum(self):
        """Test DataFrequency enum."""
        assert hasattr(eranest.DataFrequency, "HOURLY")
        assert hasattr(eranest.DataFrequency, "DAILY")
        assert hasattr(eranest.DataFrequency, "MONTHLY")

    def test_geojson_validation(self):
        """Test GeoJSON validation."""
        valid_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                    },
                    "properties": {},
                }
            ],
        }

        assert eranest.validate_geojson(valid_geojson) == True

        # Invalid GeoJSON should raise exception in strict mode (default)
        invalid_geojson = {"type": "InvalidType"}
        with pytest.raises(ValidationError):
            eranest.validate_geojson(invalid_geojson)

        # In non-strict mode, should return False
        assert eranest.validate_geojson(invalid_geojson, strict=False) == False

    def test_bounding_box_extraction(self):
        """Test bounding box extraction."""
        geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]],
            },
        }

        bbox = eranest.extract_bounding_box(geojson)
        assert len(bbox) == 4
        assert bbox[0] == 0  # min_x
        assert bbox[1] == 0  # min_y
        assert bbox[2] == 2  # max_x
        assert bbox[3] == 2  # max_y

    @patch("eranest.download.era5.ERA5Downloader")
    def test_download_surface_data_mock(self, mock_downloader):
        """Test surface data download with mocked downloader."""
        mock_instance = MagicMock()
        mock_downloader.return_value = mock_instance
        mock_instance.download.return_value = "test_file.nc"

        result = eranest.download_surface_data(
            request_id="test",
            variables=["2m_temperature"],
            start_date=dt.datetime(2024, 1, 1),
            end_date=dt.datetime(2024, 1, 2),
            north=30,
            south=20,
            east=80,
            west=70,
        )

        assert result == "test_file.nc"
        mock_instance.download.assert_called_once()

    def test_no_legacy_functions(self):
        """Test that legacy functions are not available."""
        legacy_functions = ["era5ify_geojson", "era5ify_bbox"]

        for func_name in legacy_functions:
            assert not hasattr(
                eranest, func_name
            ), f"Legacy function still available: {func_name}"


class TestExceptions:
    """Test custom exceptions."""

    def test_exception_hierarchy(self):
        """Test that custom exceptions are available."""
        assert hasattr(eranest, "EranestError")
        assert hasattr(eranest, "ValidationError")
        assert hasattr(eranest, "DataDownloadError")
        assert hasattr(eranest, "DataProcessingError")

        # Test inheritance
        assert issubclass(eranest.ValidationError, eranest.EranestError)
        assert issubclass(eranest.DataDownloadError, eranest.EranestError)


class TestAuroraIntegration:
    """Test Aurora integration features."""

    def test_aurora_functions_available(self):
        """Test Aurora-specific functions."""
        assert hasattr(eranest, "create_aurora_batch")
        assert callable(eranest.create_aurora_batch)

        # Test Aurora constants
        assert len(AURORA_PRESSURE_LEVELS) > 0
        assert all(isinstance(level, str) for level in AURORA_PRESSURE_LEVELS)

    def test_aurora_converter_available(self):
        """Test Aurora converter class."""
        from eranest.aurora import AuroraConverter

        assert AuroraConverter is not None


if __name__ == "__main__":
    pytest.main([__file__])
