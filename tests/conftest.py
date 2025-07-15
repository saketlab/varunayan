import datetime as dt
import json
import os
import shutil
import tempfile
from unittest.mock import MagicMock

import pytest

from varunayan.core import ProcessingParams


@pytest.fixture
def temp_dir():
    """Create and cleanup a temporary directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_geojson():
    """Sample GeoJSON data for testing"""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-122.5, 37.5],
                            [-122.0, 37.5],
                            [-122.0, 38.0],
                            [-122.5, 38.0],
                            [-122.5, 37.5],
                        ]
                    ],
                },
            }
        ],
    }


@pytest.fixture
def sample_geojson_file(sample_geojson, temp_dir):
    """Save sample GeoJSON to a temporary file"""
    file_path = os.path.join(temp_dir, "test.geojson")
    with open(file_path, "w") as f:
        json.dump(sample_geojson, f)
    return file_path


@pytest.fixture
def basic_params():
    """Basic ProcessingParams for testing"""
    return ProcessingParams(
        request_id="test_request",
        variables=["2m_temperature", "total_precipitation"],
        start_date=dt.datetime(2020, 1, 1),
        end_date=dt.datetime(2020, 1, 2),
        frequency="hourly",
        resolution=0.25,
        north=21.0,
        south=20.5,
        east=80.0,
        west=80.5,
    )


@pytest.fixture
def basic_params_mo():
    """Basic ProcessingParams for testing monthly processes"""
    return ProcessingParams(
        request_id="test_request_mo",
        variables=["2m_temperature", "total_precipitation"],
        start_date=dt.datetime(2020, 1, 1),
        end_date=dt.datetime(2020, 12, 31),
        frequency="monthly",
        resolution=0.25,
        north=21.0,
        south=20.5,
        east=80.0,
        west=80.5,
    )


@pytest.fixture
def pressure_params():
    """ProcessingParams with pressure levels for testing"""
    return ProcessingParams(
        request_id="test_pressure",
        variables=["relative_humidity", "specific_humidity"],
        start_date=dt.datetime(2020, 1, 1),
        end_date=dt.datetime(2020, 1, 2),
        frequency="hourly",
        resolution=0.25,
        dataset_type="pressure",
        pressure_levels=["500", "850"],
        north=38.0,
        south=37.5,
        east=-122.0,
        west=-122.5,
    )


@pytest.fixture
def mock_dataframe():
    """Create a mock DataFrame for testing"""
    mock_df = MagicMock()
    mock_df.shape = (100, 5)
    mock_df.columns = [
        "time", "latitude", "longitude", "temperature", "humidity"
    ]
    return mock_df


@pytest.fixture
def sample_geojson_file_cli():
    """Create a temporary GeoJSON file for testing"""
    geojson_content = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-74.0, 40.7],
                            [-74.0, 40.8],
                            [-73.9, 40.8],
                            [-73.9, 40.7],
                            [-74.0, 40.7],
                        ]
                    ],
                },
                "properties": {"name": "Test Region", "id": 1},
            }
        ],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".geojson", delete=False
    ) as f:
        json.dump(geojson_content, f)
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def sample_json_file():
    """Create a temporary JSON file for testing"""
    json_content = {
        "regions": [
            {
                "name": "Region 1",
                "bounds": {
                    "north": 40.8,
                    "south": 40.7,
                    "east": -73.9,
                    "west": -74.0,
                },
            }
        ]
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(json_content, f)
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def cli_base_args():
    """Base CLI arguments used in multiple tests"""
    return {
        "request_id": "test-request-123",
        "variables": "temperature,humidity",
        "start": "2023-01-01",
        "end": "2023-01-31",
        "dataset_type": "single",
        "freq": "hourly",
        "res": 0.25,
    }


@pytest.fixture
def bbox_coords():
    """Sample bounding box coordinates"""
    return {"north": 40.8, "south": 40.7, "east": -73.9, "west": -74.0}


@pytest.fixture
def point_coords():
    """Sample point coordinates"""
    return {"lat": 40.7589, "lon": -73.9851}


@pytest.fixture(params=["hourly", "daily", "weekly", "monthly", "yearly"])
def frequency_options(request):
    """Parametrized fixture for frequency options"""
    return request.param


@pytest.fixture(params=["single", "pressure"])
def dataset_type_options(request):
    """Parametrized fixture for dataset type options"""
    return request.param


@pytest.fixture
def pressure_levels():
    """Sample pressure levels"""
    return ["1000", "925", "850", "700", "500", "300", "200", "100"]


@pytest.fixture
def variable_combinations():
    """Various variable combinations for testing"""
    return [
        ["temperature"],
        ["temperature", "humidity"],
        ["temperature", "humidity", "wind_speed"],
        ["pressure", "geopotential_height"],
        ["u_wind", "v_wind", "temperature", "humidity"],
    ]


# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


# Custom assertions
def assert_dataframe_called_with_args(mock_func, expected_args):
    """Helper function to assert that a function was called with expected
    arguments"""
    mock_func.assert_called_once()
    call_args = mock_func.call_args[1]

    for key, expected_value in expected_args.items():
        assert key in call_args, f"Expected argument '{key}' not found in call"
        assert (
            call_args[key] == expected_value
        ), f"Expected {key}={expected_value}, got {call_args[key]}"
