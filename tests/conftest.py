import pytest
import os
import tempfile
import shutil
import json
import datetime as dt
from shapely.geometry import Polygon
from eranest.core import ProcessingParams

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
                    "coordinates": [[
                        [-122.5, 37.5],
                        [-122.0, 37.5],
                        [-122.0, 38.0],
                        [-122.5, 38.0],
                        [-122.5, 37.5]
                    ]]
                }
            }
        ]
    }

@pytest.fixture
def sample_geojson_file(sample_geojson, temp_dir):
    """Save sample GeoJSON to a temporary file"""
    file_path = os.path.join(temp_dir, "test.geojson")
    with open(file_path, 'w') as f:
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
        west=80.5
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
        pressure_levels=["500", "850"],
        north=38.0,
        south=37.5,
        east=-122.0,
        west=-122.5
    )