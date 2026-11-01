import datetime as dt
import tempfile
import zipfile
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import varunayan
from varunayan.core import cleanup_temp_files
from varunayan.download import download_era5_pressure_lvl, download_era5_single_lvl


@patch("varunayan.download.era5_downloader.cdsapi.Client")
def test_download_era5_single_lvl(mock_client: MagicMock):
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
        frequency="hourly",
    )

    assert isinstance(result, str)
    assert result.endswith(".zip")


@patch("varunayan.download.era5_downloader.cdsapi.Client")
def test_download_era5_single_lvl_mo(mock_client: MagicMock):
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
        frequency="monthly",
    )

    assert isinstance(result, str)
    assert result.endswith(".zip")


@patch("varunayan.download.era5_downloader.cdsapi.Client")
def test_download_era5_pressure_lvl(mock_client: MagicMock):
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
        pressure_levels=["500", "850"],
    )

    assert isinstance(result, str)
    assert result.endswith(".nc")


@patch("varunayan.download.era5_downloader.cdsapi.Client")
def test_download_era5_pressure_lvl_mo(mock_client: MagicMock):
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
        pressure_levels=["500", "850"],
    )

    assert isinstance(result, str)
    assert result.endswith(".nc")


def _fake_timeseries_zip(dataset, request, target):
    assert dataset == "reanalysis-era5-single-levels-timeseries"
    assert request["location"] == {"latitude": 19.07, "longitude": 72.87}
    assert request["date"] == ["2023-01-01/2023-01-01"]
    csv = (
        "valid_time,t2m,tp,latitude,longitude\n"
        "1940-01-01 06:00:00,,,19.0,72.75\n"  # before ERA5 starts: empty
        "2023-01-01 00:00:00,300.15,0.002,19.0,72.75\n"
        "2023-01-01 01:00:00,299.15,0.0,19.0,72.75\n"
    )
    with zipfile.ZipFile(target, "w") as z:
        z.writestr("series.csv", csv)


@patch("varunayan.download.era5_downloader.cdsapi.Client")
def test_era5ify_point_hourly_uses_timeseries_endpoint(mock_client: MagicMock):
    mock_client.return_value.retrieve.side_effect = _fake_timeseries_zip
    df = varunayan.era5ify_point(
        "ts", ["2m_temperature", "total_precipitation"],
        "2023-01-01", "2023-01-01", 19.07, 72.87,
    )  # fmt: skip
    assert len(df) == 4  # 2 hours x 2 variables; the empty row is dropped
    t2m = df[df["variable"] == "t2m"]["value"].round(6).tolist()
    tp = df[df["variable"] == "tp"]["value"].round(6).tolist()
    assert t2m == [27.0, 26.0]  # Celsius
    assert tp == [2.0, 0.0]  # mm
    assert set(df["latitude"]) == {19.0} and set(df["longitude"]) == {72.75}


@patch("varunayan.core.process_era5")
@patch("varunayan.download.era5_downloader.cdsapi.Client")
def test_era5ify_point_falls_back_to_gridded_download(
    mock_client: MagicMock, mock_process: MagicMock
):
    mock_client.return_value.retrieve.side_effect = RuntimeError("endpoint down")
    mock_process.return_value = pd.DataFrame(
        {"latitude": [19.0], "longitude": [72.75], "variable": ["t2m"], "value": [1.0]}
    )
    df = varunayan.era5ify_point(
        "ts", ["2m_temperature"], "2023-01-01", "2023-01-01", 19.07, 72.87
    )
    assert mock_process.called and len(df) == 1


def test_era5ify_point_timeseries_only_for_hourly_single_level():
    with pytest.raises(ValueError):
        varunayan.era5ify_point(
            "ts", ["2m_temperature"], "2023-01-01", "2023-01-02", 19.0, 72.0,
            frequency="daily", use_timeseries_api=True,
        )  # fmt: skip


def test_cleanup_temp_files_removes_only_this_requests_files(tmp_path, monkeypatch):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    own = ["ts.zip", "ts.nc", "ts_chunk2.zip", "ts", "ts_chunk2"]
    other = ["com.apple.LiveEntityService", "ts_other", "xts.zip", "ts_chunkX"]
    for name in own + other:
        path = tmp_path / name
        path.mkdir() if "." not in name else path.write_text("x")
    geojson = tmp_path / "ts_temp_geojson.json"
    geojson.write_text("{}")
    cleanup_temp_files("ts", str(geojson))
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(other)
