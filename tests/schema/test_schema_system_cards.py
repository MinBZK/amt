import pytest
from amt.schema.system_card import SystemCard
from tests.constants import default_systemcard_dic


@pytest.fixture
def setup() -> SystemCard:
    system_card = SystemCard()  # pyright: ignore[reportCallIssue]
    return system_card


def test_get_system_card(setup: SystemCard) -> None:
    system_card = setup
    assert system_card.model_dump() == default_systemcard_dic()


def test_system_card_update(setup: SystemCard) -> None:
    system_card = setup
    expected = default_systemcard_dic()
    expected["name"] = "IAMA 1.1"
    system_card.name = "IAMA 1.1"
    assert system_card.model_dump(exclude_none=False) == expected
