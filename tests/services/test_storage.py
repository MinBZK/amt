from pathlib import Path

import pytest
from amt.core.exceptions import AMTKeyError, AMTValueError
from amt.schema.system_card import SystemCard
from amt.services.storage import StorageFactory
from yaml import safe_load


@pytest.fixture
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
    with pytest.raises(AMTKeyError, match="Key not correct"):
        StorageFactory.init(storage_type="file", filename=filename)  # pyright: ignore [reportCallIssue]


def test_file_system_writer_no_filename_variable(setup_and_teardown: tuple[str, Path]) -> None:
    _, location = setup_and_teardown
    with pytest.raises(AMTKeyError, match="Key not correct"):
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
    data = SystemCard()  # pyright: ignore[reportCallIssue]
    data.name = "test"
    data_dict = data.model_dump()

    storage_writer = StorageFactory.init(storage_type="file", location=location, filename=filename)
    storage_writer.write(data_dict)

    with open(Path(location) / filename) as f:
        assert safe_load(f) == data_dict, True


def test_abstract_writer_non_yaml_filename(setup_and_teardown: tuple[str, Path]) -> None:
    _, location = setup_and_teardown
    filename = "test.csv"
    with pytest.raises(AMTValueError, match="Value not correct"):
        StorageFactory.init(storage_type="file", location=location, filename=filename)


def test_not_valid_writer_type() -> None:
    writer_type = "kafka"
    with pytest.raises(AMTValueError, match="Value not correct"):
        StorageFactory.init(storage_type=writer_type)  # pyright: ignore [reportCallIssue]


def test_file_system_reader() -> None:
    location = "tests/services/data/"
    filename = "test.yaml"
    storage_reader = StorageFactory.init(storage_type="file", location=location, filename=filename)
    data = storage_reader.read()

    assert data == {"test": "test"}
