import pytest
from tad.models.system_card import SystemCard


@pytest.fixture()
def setup():
    system_card = SystemCard()
    return system_card


def test_get_system_card(setup):
    system_card = setup
    expected = {"title": None}

    assert system_card.dict() == expected


def test_system_card_update(setup):
    system_card = setup
    expected = {"title": "IAMA 1.1"}
    system_card.title = "IAMA 1.1"

    assert system_card.dict() == expected
