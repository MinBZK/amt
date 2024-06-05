import shutil
from pathlib import Path

import pytest
from tad.models.system_card import SystemCard
from tad.services.storage import WriterFactory
from yaml import safe_load


@pytest.fixture()
def setup_and_teardown():
    filename = "test.yaml"
    location = "./tests/data"
    loc_path = Path(location)
    Path.mkdir(loc_path, exist_ok=True)

    yield filename, location

    shutil.rmtree(loc_path)


def test_file_system_writer_empty_yaml(setup_and_teardown):
    filename, location = setup_and_teardown

    storage_writer = WriterFactory.get_writer(writer_type="file", location=location, filename=filename)
    storage_writer.write({})

    assert Path.is_file(Path(location) / filename), True


def test_file_system_writer_no_location_variable(setup_and_teardown):
    filename, _ = setup_and_teardown
    with pytest.raises(
        KeyError, match="The `location` or `filename` variables are not provided as input for get_writer()"
    ):
        WriterFactory.get_writer(writer_type="file", filename=filename)


def test_file_system_writer_no_filename_variable(setup_and_teardown):
    _, location = setup_and_teardown
    with pytest.raises(
        KeyError, match="The `location` or `filename` variables are not provided as input for get_writer()"
    ):
        WriterFactory.get_writer(writer_type="file", location=location)


def test_file_system_writer_yaml_with_content(setup_and_teardown):
    filename, location = setup_and_teardown
    data = {"test": "test"}
    storage_writer = WriterFactory.get_writer(writer_type="file", location=location, filename=filename)
    storage_writer.write(data)

    with open(Path(location) / filename) as f:
        assert safe_load(f) == data, True


def test_file_system_writer_with_system_card(setup_and_teardown):
    filename, location = setup_and_teardown
    data = SystemCard()
    data.title = "test"
    data_dict = data.dict()

    storage_writer = WriterFactory.get_writer(writer_type="file", location=location, filename=filename)
    storage_writer.write(data_dict)

    with open(Path(location) / filename) as f:
        assert safe_load(f) == data_dict, True


def test_abstract_writer_non_yaml_filename(setup_and_teardown):
    _, location = setup_and_teardown
    filename = "test.csv"
    with pytest.raises(
        ValueError, match=f"Filename {filename} must end with .yaml instead of .{filename.split('.')[-1]}"
    ):
        WriterFactory.get_writer(writer_type="file", location=location, filename=filename)


def test_non_dict_data():
    pass


def test_git_writer():
    pass


def test_s3_writer():
    pass
