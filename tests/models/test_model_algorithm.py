import json
from datetime import UTC, datetime
from enum import Enum

from amt.models.algorithm import Algorithm, CustomJSONEncoder
from amt.schema.system_card import SystemCard


def test_model_basic_algorithm():
    # given
    algorithm = Algorithm(name="Test Algorithm")

    # then
    assert algorithm.name == "Test Algorithm"


def test_model_systemcard():
    # given
    system_card = SystemCard(name="Test System Card")  # pyright: ignore[reportCallIssue]

    algorithm = Algorithm(name="Test Algorithm", system_card=system_card)

    # then
    assert algorithm.system_card is not None
    assert algorithm.system_card.name == "Test System Card"


def test_model_systemcard_full():
    # given
    system_card = SystemCard(name="Test System Card", description="Test description", status="active")  # pyright: ignore[reportCallIssue]

    algorithm = Algorithm(name="Test Algorithm")
    algorithm.system_card = system_card

    # then
    assert algorithm.system_card is not None
    assert algorithm.system_card.name == "Test System Card"
    assert algorithm.system_card.description == "Test description"
    assert algorithm.system_card.status == "active"

    # when
    algorithm.system_card.name = "Another name"

    # then
    assert algorithm.system_card.name == "Another name"
    assert algorithm.system_card_json["name"] == "Another name"


def test_model_systemcard_direct():
    # given
    algorithm = Algorithm(name="Test Algorithm")
    algorithm.system_card.name = "Test System Card"

    # then
    assert algorithm.system_card.name == "Test System Card"


def test_model_systemcard_equal():
    # given
    system_card = SystemCard(name="Test System Card", description="Test description", status="active")  # pyright: ignore[reportCallIssue]
    algorithm = Algorithm(name="Test Algorithm", system_card=system_card)

    # then
    assert algorithm.system_card.name == "Test System Card"
    assert algorithm.system_card == system_card
    assert system_card == algorithm.system_card

    # when
    algorithm.system_card.name = "Another name"

    # then
    assert algorithm.system_card != system_card
    assert algorithm.system_card != {}


def test_model_systemcard_from_json():
    # given
    algorithm = Algorithm(name="Test Algorithm")

    # when
    algorithm.system_card_json = {"name": "Test System Card"}

    # then
    assert algorithm.system_card == SystemCard(name="Test System Card")  # pyright: ignore[reportCallIssue]


def test_model_systemcard_none():
    # given
    algorithm = Algorithm(name="Test Algorithm")

    # when
    algorithm.system_card = None

    # then
    assert algorithm.system_card == SystemCard()  # pyright: ignore[reportCallIssue]


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
