import pytest
import datetime as dt
from unittest.mock import patch, MagicMock
from eranest.download import (
    download_era5_single_lvl,
    download_era5_pressure_lvl
)

@patch('eranest.download.era5_downloader.cdsapi.Client')
def test_download_era5_single_lvl(mock_client):
    mock_client.return_value.retrieve.return_value = MagicMock()
    mock_client.return_value.retrieve.return_value.download.return_value = None
    
    # This is a mock test - actual downloads would require CDS API credentials
    result = download_era5_single_lvl(
        request_id="test",
        variables=["t2m"],
        start_date=dt.datetime(year=2020, month=1, day=1),
        end_date=dt.datetime(year=2020, month=1, day=2), 
        north=38.0,
        south=37.5,
        east=-122.0,
        west=-122.5,
        resolution=0.25,
        frequency="hourly"
    )
    
    assert isinstance(result, str)
    assert result.endswith(".zip")

@patch('eranest.download.era5_downloader.cdsapi.Client')
def test_download_era5_single_lvl_mo(mock_client):
    mock_client.return_value.retrieve.return_value = MagicMock()
    mock_client.return_value.retrieve.return_value.download.return_value = None
    
    # This is a mock test - actual downloads would require CDS API credentials
    result = download_era5_single_lvl(
        request_id="test",
        variables=["t2m"],
        start_date=dt.datetime(year=2020, month=1, day=1),
        end_date=dt.datetime(year=2020, month=12, day=31), 
        north=38.0,
        south=37.5,
        east=-122.0,
        west=-122.5,
        resolution=0.25,
        frequency="monthly"
    )
    
    assert isinstance(result, str)
    assert result.endswith(".zip")

@patch('eranest.download.era5_downloader.cdsapi.Client')
def test_download_era5_pressure_lvl(mock_client):
    mock_client.return_value.retrieve.return_value = MagicMock()
    mock_client.return_value.retrieve.return_value.download.return_value = None
    
    result = download_era5_pressure_lvl(
        request_id="test",
        variables=["z"],
        start_date=dt.datetime(year=2020, month=1, day=1),
        end_date=dt.datetime(year=2020, month=1, day=2),
        north=38.0,
        south=37.5,
        east=-122.0,
        west=-122.5,
        resolution=0.25,
        frequency="hourly",
        pressure_levels=["500", "850"]
    )
    
    assert isinstance(result, str)
    assert result.endswith(".nc")

@patch('eranest.download.era5_downloader.cdsapi.Client')
def test_download_era5_pressure_lvl_mo(mock_client):
    mock_client.return_value.retrieve.return_value = MagicMock()
    mock_client.return_value.retrieve.return_value.download.return_value = None
    
    result = download_era5_pressure_lvl(
        request_id="test",
        variables=["z"],
        start_date=dt.datetime(year=2020, month=1, day=1),
        end_date=dt.datetime(year=2020, month=12, day=31),
        north=38.0,
        south=37.5,
        east=-122.0,
        west=-122.5,
        resolution=0.25,
        frequency="monthly",
        pressure_levels=["500", "850"]
    )
    
    assert isinstance(result, str)
    assert result.endswith(".nc")