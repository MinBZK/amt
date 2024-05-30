import pytest
from tad.services.system_card import SystemCardService


@pytest.fixture()
def setup():
    system_card_service = SystemCardService()
    return system_card_service


def test_get_system_card(setup):
    system_card_service = setup
    expected = {}

    assert system_card_service.get_system_card() == expected


def test_system_card_update(setup):
    system_card_service = setup
    expected = {"title": "IAMA 1.1"}
    system_card_service.update("IAMA 1.1")

    assert system_card_service.get_system_card() == expected
