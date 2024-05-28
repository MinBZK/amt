import pytest
from yaml import safe_load
from tad.services.writer import FileSystemWriter, S3Writer, GitWriter
from pathlib import Path

FILENAME = "test.yaml"
LOCATION = "./tests/data"


@pytest.fixture(autouse=True)
def cleanup_test_yaml():
    yield
    file = Path(LOCATION) / FILENAME
    if Path.is_file(file):
        Path.unlink(file)


def test_file_system_writer_empty_yaml():
    data = {}
    file_system_writer = FileSystemWriter(data, LOCATION, FILENAME)
    file_system_writer.write()

    assert Path.is_file(Path(LOCATION) / FILENAME), True


def test_file_system_writer_yaml_with_content():
    data = {"test": "test"}
    file_system_writer = FileSystemWriter(data, LOCATION, FILENAME)
    file_system_writer.write()

    with open(Path(LOCATION) / FILENAME, "r") as f:
        assert safe_load(f) == data, True


def test_abstract_writer_non_yaml_filename():
    data = {"test": "test"}
    filename = "test.csv"
    with pytest.raises(ValueError):
        FileSystemWriter(data, LOCATION, filename)

def test_git_writer():
    pass


def test_s3_writer():
    pass
