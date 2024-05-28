import shutil
from pathlib import Path

import pytest
from tad.services.storage import FileSystemWriteService
from yaml import safe_load


@pytest.mark.skip(reason="This is an initialisation function for the tests")
def init():
    filename = "test.yaml"
    location = "./tests/data"
    return filename, location


@pytest.fixture(autouse=True)
def _cleanup_test_yaml() -> None:
    _, location = init()
    loc_path = Path(location)
    Path.mkdir(loc_path, exist_ok=True)
    yield
    shutil.rmtree(loc_path)


def test_file_system_writer_empty_yaml():
    filename, location = init()
    file_system_writer = FileSystemWriteService(location, filename)
    file_system_writer.write({})

    assert Path.is_file(Path(location) / filename), True


def test_file_system_writer_yaml_with_content():
    filename, location = init()
    data = {"test": "test"}
    file_system_writer = FileSystemWriteService(location, filename)
    file_system_writer.write(data)

    with open(Path(location) / filename) as f:
        assert safe_load(f) == data, True


def test_abstract_writer_non_yaml_filename():
    _, location = init()
    filename = "test.csv"
    with pytest.raises(ValueError,
                       match=f"Filename {filename} must end with .yaml instead of .{filename.split('.')[-1]}"):
        FileSystemWriteService(location, filename)


def test_non_dict_data():
    pass


def test_git_writer():
    pass


def test_s3_writer():
    pass