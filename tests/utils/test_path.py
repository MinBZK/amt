from pathlib import Path

from amt.utils.path import is_safe_path


def test_utils_path_is_safe_path():
    # given
    basedir = Path("/test/")
    path = Path("/test/") / "test.yaml"

    # when
    result = is_safe_path(basedir, path)

    # then
    assert result is True


def test_utils_path_is_not_safe_path():
    # given
    basedir = Path("/test/")
    path = Path("/test/") / "../test.yaml"

    # when
    result = is_safe_path(basedir, path)

    # then
    assert result is False


def test_utils_path_is_same_safe_path():
    # given
    basedir = Path("/test/")
    path = Path("/test/")

    # when
    result = is_safe_path(basedir, path)

    # then
    assert result is True
