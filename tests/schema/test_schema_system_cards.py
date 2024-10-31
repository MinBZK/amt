from typing import Any

import pytest
from amt.schema.system_card import SystemCard


@pytest.fixture
def setup() -> SystemCard:
    system_card = SystemCard()
    return system_card


def test_get_system_card(setup: SystemCard) -> None:
    system_card = setup
    expected: dict[str, str | list[Any] | None] = {
        "schema_version": "0.1a10",
        "name": None,
        "ai_act_profile": None,
        "provenance": {},  # pyright: ignore [reportAssignmentType]
        "description": None,
        "labels": [],
        "status": None,
        "instruments": [],
        "assessments": [],
        "requirements": [],
        "measures": [],
        "references": [],
        "models": [],
    }

    assert system_card.model_dump() == expected


def test_system_card_update(setup: SystemCard) -> None:
    system_card = setup
    expected: dict[str, str | list[Any] | None] = {
        "schema_version": "0.1a10",
        "name": "IAMA 1.1",
        "provenance": {},  # pyright: ignore [reportAssignmentType]
        "labels": [],
        "instruments": [],
        "assessments": [],
        "requirements": [],
        "measures": [],
        "references": [],
        "models": [],
    }
    system_card.name = "IAMA 1.1"
    assert system_card.model_dump(exclude_none=True) == expected
