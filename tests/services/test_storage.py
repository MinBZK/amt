from pathlib import Path

import pytest
from amt.schema.system_card import SystemCard
from amt.services.storage import StorageFactory
from yaml import safe_load


@pytest.fixture()
def setup_and_teardown(tmp_path: Path) -> tuple[str, Path]:
    filename = "test.yaml"
    return filename, tmp_path.absolute()


def test_file_system_writer_empty_yaml(setup_and_teardown: tuple[str, Path]) -> None:
    filename, location = setup_and_teardown

    storage_writer = StorageFactory.init(storage_type="file", location=location, filename=filename)
    storage_writer.write({})

    assert Path.is_file(Path(location) / filename), True


def test_file_system_writer_no_location_variable(setup_and_teardown: tuple[str, Path]) -> None:
    filename, _ = setup_and_teardown
    with pytest.raises(KeyError, match="The `location` or `filename` variables are not provided as input for init()"):
        StorageFactory.init(storage_type="file", filename=filename)  # pyright: ignore [reportCallIssue]


def test_file_system_writer_no_filename_variable(setup_and_teardown: tuple[str, Path]) -> None:
    _, location = setup_and_teardown
    with pytest.raises(KeyError, match="The `location` or `filename` variables are not provided as input for init()"):
        StorageFactory.init(storage_type="file", location=location)  # pyright: ignore [reportCallIssue]


def test_file_system_writer_yaml_with_content(setup_and_teardown: tuple[str, Path]) -> None:
    filename, location = setup_and_teardown
    data = {"test": "test"}
    storage_writer = StorageFactory.init(storage_type="file", location=location, filename=filename)
    storage_writer.write(data)

    with open(Path(location) / filename) as f:
        assert safe_load(f) == data, True


def test_file_system_writer_yaml_with_content_in_dir(setup_and_teardown: tuple[str, Path]) -> None:
    filename, location = setup_and_teardown
    data = {"test": "test"}

    new_location = Path(location) / "new_dir"
    storage_writer = StorageFactory.init(storage_type="file", location=new_location, filename=filename)
    storage_writer.write(data)

    with open(new_location / filename) as f:
        assert safe_load(f) == data, True


def test_file_system_writer_with_system_card(setup_and_teardown: tuple[str, Path]) -> None:
    filename, location = setup_and_teardown
    data = SystemCard()
    data.name = "test"
    data_dict = data.model_dump()

    storage_writer = StorageFactory.init(storage_type="file", location=location, filename=filename)
    storage_writer.write(data_dict)

    with open(Path(location) / filename) as f:
        assert safe_load(f) == data_dict, True


def test_abstract_writer_non_yaml_filename(setup_and_teardown: tuple[str, Path]) -> None:
    _, location = setup_and_teardown
    filename = "test.csv"
    with pytest.raises(
        ValueError, match=f"Filename {filename} must end with .yaml instead of .{filename.split('.')[-1]}"
    ):
        StorageFactory.init(storage_type="file", location=location, filename=filename)


def test_not_valid_writer_type() -> None:
    writer_type = "kafka"
    with pytest.raises(ValueError, match=f"Unknown storage type: {writer_type}"):
        StorageFactory.init(storage_type=writer_type)  # pyright: ignore [reportCallIssue]


def test_file_system_reader() -> None:
    location = "tests/services/data/"
    filename = "test.yaml"
    storage_reader = StorageFactory.init(storage_type="file", location=location, filename=filename)
    data = storage_reader.read()

    assert data == {"test": "test"}
