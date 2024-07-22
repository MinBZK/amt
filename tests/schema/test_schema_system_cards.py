from typing import Any

import pytest
from tad.schema.system_card import SystemCard


@pytest.fixture()
def setup() -> SystemCard:
    system_card = SystemCard()
    return system_card


def test_get_system_card(setup: SystemCard) -> None:
    system_card = setup
    expected: dict[str, str | list[Any] | None] = {
        "name": None,
        "schema_version": "0.1a6",
        "selected_instruments": [],
        "assessments": [],
    }

    assert system_card.model_dump() == expected


def test_system_card_update(setup: SystemCard) -> None:
    system_card = setup
    expected: dict[str, str | list[Any] | None] = {
        "name": "IAMA 1.1",
        "schema_version": "0.1a6",
        "selected_instruments": [],
        "assessments": [],
    }
    system_card.name = "IAMA 1.1"

    assert system_card.model_dump(exclude_none=True) == expected
