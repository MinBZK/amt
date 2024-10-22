import os
from pathlib import Path
from typing import NamedTuple

import pytest
from amt.api import http_browser_caching
from amt.core.exceptions import AMTNotFound, AMTOnlyStatic
from starlette.responses import Response


def test_url_for_cache_not_static():
    with pytest.raises(AMTOnlyStatic, match="Only static files are supported."):
        http_browser_caching.url_for_cache("not-static")


def test_url_for_cache_not_local():
    with pytest.raises(AMTOnlyStatic, match="Only static files are supported."):
        http_browser_caching.url_for_cache("static", path="http://this.is.not.local")


def test_url_for_cache_file_not_found():
    with pytest.raises(AMTNotFound, match="The requested page or resource could not be found."):
        http_browser_caching.url_for_cache("static", path="this/does/not/exist")


def test_url_for_cache_file_happy_flow(tmp_path: Path, mocker):
    class MockStatResult(NamedTuple):
        st_mtime: int
        st_size: int

    (tmp_path / "testfile").write_text("This is a test", encoding="utf-8")
    http_browser_caching.static_files = http_browser_caching.StaticFilesCache(directory=Path(tmp_path))
    mocker.patch('amt.api.http_browser_caching.static_files.lookup_path', return_value=(None, MockStatResult(1, 2)))
    result = http_browser_caching.url_for_cache("static", path="testfile")
    assert result == "/static/testfile?etag=98c6f2c2287f4c73cea3d40ae7ec3ff2"
    # also test with a query param
    result = http_browser_caching.url_for_cache("static", path="testfile?queryparam1=true")
    assert result == "/static/testfile?queryparam1=true&etag=98c6f2c2287f4c73cea3d40ae7ec3ff2"

def test_static_files_class_immutable(tmp_path: Path):
    testfile = tmp_path / "testfile"
    testfile.write_text("This is a test", encoding="utf-8")
    static_files = http_browser_caching.StaticFilesCache(directory=Path(tmp_path))
    stat_result = os.stat(testfile)
    response: Response = static_files.file_response(  #  pyright: ignore [reportUnknownMemberType]
        testfile, stat_result, {"headers": [], "query_string": b"etag=value-for-testing"}
    )
    assert b"cache-control", b"public, max-age=31536000, immutable" in response.headers


def test_static_files_class_temporary(tmp_path: Path):
    testfile = tmp_path / "testfile"
    testfile.write_text("This is a test", encoding="utf-8")
    static_files = http_browser_caching.StaticFilesCache(directory=Path(tmp_path))
    stat_result = os.stat(testfile)
    response: Response = static_files.file_response(testfile, stat_result, {"headers": [], "query_string": b""})  #  pyright: ignore [reportUnknownMemberType]
    assert b"cache-control", b"public, max-age=3600, must-revalidate" in response.headers
