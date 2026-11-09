import datetime as dt
import gzip
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import zipfile

import pandas as pd
import pytest
import requests

from varunayan._geo_utils import download_and_decompress_gz
from varunayan.cache import _load_cache_metadata, _save_cache_metadata
from varunayan.config import CDSSetupError, ensure_cdsapi_config
from varunayan.imd import download_imd_rainfall
from varunayan.live_cli import _report_error
from varunayan.processing import extract_download
from varunayan.core import (
    CDSAuthError,
    ProcessingParams,
    download_with_retry,
    process_time_chunks,
)


def _params() -> ProcessingParams:
    return ProcessingParams(
        request_id="r",
        variables=["2m_temperature"],
        start_date=dt.datetime(2020, 1, 1),
        end_date=dt.datetime(2020, 1, 28),
    )


def test_import_needs_no_credentials(tmp_path: Path) -> None:
    env = {k: v for k, v in os.environ.items() if "CDS" not in k}
    env["HOME"] = str(tmp_path)
    done = subprocess.run(
        [sys.executable, "-c", "import varunayan"],
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=120,
    )
    assert done.returncode == 0, done.stderr
    assert not (tmp_path / ".cdsapirc").exists()


def test_lost_chunk_is_named_in_a_warning() -> None:
    params = _params()
    frames = [pd.DataFrame({"a": [1]}), RuntimeError("boom")]
    process = MagicMock(side_effect=frames)
    with pytest.warns(UserWarning, match="missing 1 of 2 chunks: 2020-01-15"):
        result = process_time_chunks(params, MagicMock(), process)
    assert len(result) == 1
    assert params.failed_chunks == ["2020-01-15 to 2020-01-28"]


def test_refused_credentials_stop_at_once() -> None:
    download = MagicMock(side_effect=RuntimeError("401 Unauthorized"))
    with patch("varunayan.core.time.sleep") as sleep:
        with pytest.raises(CDSAuthError):
            download_with_retry(download, _params())
    assert download.call_count == 1
    sleep.assert_not_called()


def test_auth_failure_is_not_skipped_as_a_lost_chunk() -> None:
    process = MagicMock(side_effect=CDSAuthError("no"))
    with pytest.raises(CDSAuthError):
        process_time_chunks(_params(), MagicMock(), process)
    assert process.call_count == 1


@patch("varunayan._geo_utils.requests.get")
def test_bad_gzip_leaves_no_cached_file(get: MagicMock, tmp_path: Path) -> None:
    get.return_value = MagicMock(iter_content=lambda chunk_size: [b"not gzip"])
    with pytest.raises(gzip.BadGzipFile):
        download_and_decompress_gz("https://x/file.nc.gz", str(tmp_path))
    assert not (tmp_path / "file.nc").exists()


def test_extract_ignores_leftovers_from_a_crashed_run(tmp_path: Path) -> None:
    (tmp_path / "req").mkdir()
    (tmp_path / "req" / "stale.nc").write_bytes(b"old")
    archive = tmp_path / "req.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("new.nc", b"new")
    found = extract_download(str(archive))
    assert [Path(f).name for f in found] == ["new.nc"]


def test_corrupt_cache_index_warns_and_recovers(tmp_path: Path) -> None:
    with patch("varunayan.cache.get_cache_dir", return_value=tmp_path):
        (tmp_path / "cache_metadata.json").write_text('{"truncated":')
        with pytest.warns(UserWarning, match="corrupt cache index"):
            assert _load_cache_metadata() == {}
        _save_cache_metadata({"a": 1})
        assert _load_cache_metadata() == {"a": 1}


def test_setup_failure_raises_instead_of_exiting() -> None:
    with (
        patch("varunayan.config.check_cdsapi_config", return_value=False),
        patch("varunayan.config._get_env_credentials", return_value=None),
        patch("varunayan.config.setup_cdsapi_config", side_effect=ValueError("no")),
        patch.dict(sys.modules),
        patch.dict(os.environ, clear=True),
    ):
        sys.modules.pop("pytest", None)
        sys.modules.pop("sphinx", None)
        with pytest.raises(CDSSetupError):
            ensure_cdsapi_config()


@patch("varunayan.imd.time.sleep")
@patch("varunayan.imd.requests.post")
def test_imd_does_not_retry_a_404(
    post: MagicMock, _: MagicMock, tmp_path: Path
) -> None:
    reply = requests.Response()
    reply.status_code = 404
    post.return_value = reply
    with pytest.raises(requests.HTTPError):
        download_imd_rainfall(2020, 2020, output_dir=str(tmp_path))
    assert post.call_count == 1


def test_rich_markup_in_an_error_does_not_crash(capsys: pytest.CaptureFixture) -> None:
    args = MagicMock(json=False)
    assert _report_error(args, "[/bad] [Errno 2] missing") == 1
    assert "[/bad] [Errno 2] missing" in capsys.readouterr().err
