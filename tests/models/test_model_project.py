import json
from datetime import UTC, datetime
from enum import Enum

from amt.models.project import CustomJSONEncoder, Project
from amt.schema.system_card import SystemCard


def test_model_basic_project():
    # given
    project = Project(name="Test Project")

    # then
    assert project.name == "Test Project"


def test_model_systemcard():
    # given
    system_card = SystemCard(name="Test System Card")

    project = Project(name="Test Project", system_card=system_card)

    # then
    assert project.system_card is not None
    assert project.system_card.name == "Test System Card"


def test_model_systemcard_full():
    # given
    system_card = SystemCard(name="Test System Card", description="Test description", status="active")

    project = Project(name="Test Project")
    project.system_card = system_card

    # then
    assert project.system_card is not None
    assert project.system_card.name == "Test System Card"
    assert project.system_card.description == "Test description"
    assert project.system_card.status == "active"

    # when
    project.system_card.name = "Another name"

    # then
    assert project.system_card.name == "Another name"
    assert project.system_card_json["name"] == "Another name"


def test_model_systemcard_direct():
    # given
    project = Project(name="Test Project")
    project.system_card.name = "Test System Card"

    # then
    assert project.system_card.name == "Test System Card"


def test_model_systemcard_equal():
    # given
    system_card = SystemCard(name="Test System Card", description="Test description", status="active")
    project = Project(name="Test Project", system_card=system_card)

    # then
    assert project.system_card.name == "Test System Card"
    assert project.system_card == system_card
    assert system_card == project.system_card

    # when
    project.system_card.name = "Another name"

    # then
    assert project.system_card != system_card
    assert project.system_card != {}


def test_model_systemcard_from_json():
    # given
    project = Project(name="Test Project")

    # when
    project.system_card_json = {"name": "Test System Card"}

    # then
    assert project.system_card == SystemCard(name="Test System Card")


def test_model_systemcard_none():
    # given
    project = Project(name="Test Project")

    # when
    project.system_card = None

    # then
    assert project.system_card == SystemCard()


class TestEnum(Enum):
    A = 1
    B = 2


def test_custom_json_encoder_datetime():
    CustomJSONEncoder()
    test_datetime = datetime(2023, 5, 17, 12, 30, 45, tzinfo=UTC)
    encoded = json.dumps(test_datetime, cls=CustomJSONEncoder)
    assert encoded == '"2023-05-17T12:30:45+00:00"'


def test_custom_json_encoder_enum():
    CustomJSONEncoder()
    test_enum = TestEnum.A
    encoded = json.dumps(test_enum, cls=CustomJSONEncoder)
    assert encoded == '"A"'


def test_custom_json_encoder_standard_types():
    CustomJSONEncoder()
    test_dict = {"string": "test", "integer": 42, "float": 3.14, "list": [1, 2, 3], "bool": True, "none": None}
    encoded = json.dumps(test_dict, cls=CustomJSONEncoder)
    decoded = json.loads(encoded)
    assert decoded == test_dict


def test_custom_json_encoder_mixed_types():
    CustomJSONEncoder()
    test_data = {"datetime": datetime(2023, 5, 17, 12, 30, 45, tzinfo=UTC), "enum": TestEnum.B, "standard": "test"}
    encoded = json.dumps(test_data, cls=CustomJSONEncoder)
    decoded = json.loads(encoded)
    assert decoded == {"datetime": "2023-05-17T12:30:45+00:00", "enum": "B", "standard": "test"}
