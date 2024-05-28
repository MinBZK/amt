import pytest
from tad.services.system_card import SystemCardService


@pytest.mark.skip(reason="This is an initialisation function for the tests")
def init():
    system_card_service = SystemCardService()
    return system_card_service


def test_get_system_card():
    system_card_service = init()
    expected = {}

    assert system_card_service.get_system_card() == expected


def test_system_card_update():
    system_card_service = init()
    expected = {"title": "IAMA 1.1"}
    system_card_service.update("IAMA 1.1")

    assert system_card_service.get_system_card() == expected
