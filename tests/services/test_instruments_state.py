from datetime import datetime, timezone
from typing import Any

import pytest
from amt.schema.assessment_card import AssessmentCard
from amt.schema.instrument import InstrumentTask
from amt.schema.system_card import SystemCard
from amt.services.instruments_and_requirements_state import (
    InstrumentStateService,
    get_all_next_tasks,
    get_first_lifecycle_idx,
    get_instrument_result_from_system_card,
    get_next_tasks_per_instrument,
    get_task_timestamp_from_assessment_card,
)
from tests.constants import default_instrument

# TODO: Add more cases of the system_card for coverage


@pytest.fixture
def system_card_data_with_instruments() -> dict[str, Any]:
    return {
        "name": "test-system-card",
        "schema_version": "0.0.0",
        "instruments": [
            {"urn": "urn:nl:aivt:tr:iama:1.0"},
            {"urn": "urn:nl:aivt:tr:aiia:1.0"},
            {"urn": "urn:instrument:assessment"},
        ],
        "assessments": [
            {
                "urn": "urn:instrument:assessment",
                "contents": [{"urn": "urn:instrument:assessment:task", "timestamp": "2024-04-17T12:03:23Z"}],
            }
        ],
    }


@pytest.fixture
def system_card(system_card_data_with_instruments: dict[str, Any]) -> SystemCard:
    system_card = SystemCard(**system_card_data_with_instruments)
    return system_card


def test_get_all_next_tasks(system_card: SystemCard):
    instrument0 = default_instrument(
        urn="urn:instrument:assessment0",
        tasks=[
            InstrumentTask(question="question", urn="urn:instrument:assessment:task", lifecycle=["Ontwerp"]),
            InstrumentTask(question="question", urn="task_1_urn", lifecycle=["Ontwerp"]),
        ],
    )
    instrument1 = default_instrument(
        urn="urn:instrument:assessment1",
        tasks=[
            InstrumentTask(question="question", urn="task_2_urn", lifecycle=["Ontwerp"]),
            InstrumentTask(question="question", urn="task_3_urn", lifecycle=["Ontwerp"]),
        ],
    )
    instruments = {"urn:instrument:assessment": instrument0, "instrument1": instrument1}

    results = get_all_next_tasks(instruments, system_card)
    assert results[0]["instrument_urn"] == instrument0.urn
    assert results[0]["last_modified_date"] == system_card.assessments[0].contents[0].timestamp
    assert results[1]["instrument_urn"] == instrument1.urn
    assert results[1]["last_modified_date"] == datetime(1970, 1, 1, tzinfo=timezone.utc)  # noqa UP017


def test_get_instrument_result_from_system_card_existing(system_card: SystemCard):
    urn = system_card.assessments[0].urn
    assessment_card = system_card.assessments[0]

    assert get_instrument_result_from_system_card(urn, system_card) == assessment_card


def test_get_instrument_result_from_system_card_no_assessment_card(system_card: SystemCard):
    system_card.assessments = []
    assert get_instrument_result_from_system_card("urn", system_card) is None


def test_get_instrument_result_from_system_card_non_existing(system_card: SystemCard):
    urn = "I do not exists"

    assert not get_instrument_result_from_system_card(urn, system_card)


def test_get_task_timestamp_from_assessment_card_urn_not_found(system_card: SystemCard):
    assert not get_task_timestamp_from_assessment_card("urn", system_card.assessments[0])


def test_get_task_timestamp_from_assessment_card_existing(system_card: SystemCard):
    assessment_card = system_card.assessments[0]
    urn = system_card.assessments[0].contents[0].urn

    assert get_task_timestamp_from_assessment_card(urn, assessment_card) == datetime(
        2024,
        4,
        17,
        12,
        3,
        23,
        tzinfo=timezone.utc,  # noqa UP017
    )


def test_get_task_timestamp_from_assessment_card_non_existing(system_card: SystemCard):
    urn = "I do not exists"
    assessment_card = system_card.assessments[0]

    assert not get_task_timestamp_from_assessment_card(urn, assessment_card)


def test_get_first_lifecycle_idx_ordered():
    lifecycles = ["Ontwerp", "Monitoren"]

    assert get_first_lifecycle_idx(lifecycles) == 2


def test_get_first_lifecycle_idx_unordered():
    lifecycles = ["Monitoren", "Ontwerp"]

    assert get_first_lifecycle_idx(lifecycles=lifecycles) == 2


def test_get_first_lifecycle_empty_list():
    assert get_first_lifecycle_idx([]) == 0


def test_get_next_tasks_per_instrument_correct_urn(system_card: SystemCard):
    urn_0: str = system_card.assessments[0].urn
    assessment_card: AssessmentCard = system_card.assessments[0]
    instrument = default_instrument(urn=urn_0)

    tasks = get_next_tasks_per_instrument(instrument, assessment_card)
    assert tasks["instrument_urn"] == urn_0


def test_get_next_tasks_per_instrument_correct_timestamp_default(system_card: SystemCard):
    assessment_card: AssessmentCard = system_card.assessments[0]
    assessment_card.contents[0].timestamp = None
    urn_0 = system_card.assessments[0].urn
    urn_1 = system_card.assessments[0].contents[0].urn

    instrument = default_instrument(urn=urn_0, tasks=[InstrumentTask(urn=urn_1, lifecycle=["Ontwerp"], question="")])
    tasks = get_next_tasks_per_instrument(instrument, assessment_card)
    assert tasks["last_modified_date"] == datetime(1970, 1, 1, tzinfo=timezone.utc)  # noqa UP017


def test_get_next_tasks_per_instrument_correct_timestamp(system_card: SystemCard):
    assessment_card: AssessmentCard = system_card.assessments[0]
    urn_0 = system_card.assessments[0].urn
    urn_1 = system_card.assessments[0].contents[0].urn

    instrument = default_instrument(urn=urn_0, tasks=[InstrumentTask(question="question", urn=urn_1, lifecycle=[])])
    tasks = get_next_tasks_per_instrument(instrument, assessment_card)
    assert tasks["last_modified_date"] == datetime(2024, 4, 17, 12, 3, 23, tzinfo=timezone.utc)  # noqa UP017


def test_find_next_tasks_for_instrument_correct_lifecycle(system_card: SystemCard):
    assessment_card: AssessmentCard = system_card.assessments[0]
    assessment_card.contents[0].timestamp = None
    urn_0 = system_card.assessments[0].urn
    urn_1 = system_card.assessments[0].contents[0].urn

    test_tasks = [InstrumentTask(urn=urn_1, lifecycle=["Ontwerp"], question="")]
    instrument = default_instrument(urn=urn_0, tasks=test_tasks)
    tasks = get_next_tasks_per_instrument(instrument, assessment_card)

    assert len(tasks["tasks_per_lifecycle"]) > 0
    assert tasks["tasks_per_lifecycle"][2] == test_tasks


def test_get_state_per_instrument(system_card: SystemCard):
    instrument_state_service = InstrumentStateService(system_card)
    res = instrument_state_service.get_state_per_instrument()
    assert {"urn": "urn:nl:aivt:tr:aiia:1.0", "in_progress": 1, "name": "AI Impact Assessment (AIIA)"} in res
    assert {
        "urn": "urn:nl:aivt:tr:iama:1.0",
        "in_progress": 1,
        "name": "Impact Assessment Mensenrechten en Algoritmes (IAMA)",
    } in res
    assert {"urn": "urn:nl:aivt:tr:aiia:1.0", "in_progress": 1, "name": "AI Impact Assessment (AIIA)"} in res
    assert {"in_progress": 0, "name": "URN not found in Task Registry.", "urn": "urn:instrument:assessment"} in res


def test_get_amount_completed_instruments(system_card: SystemCard):
    instrument_state_service = InstrumentStateService(system_card)
    _ = instrument_state_service.get_state_per_instrument()
    res = instrument_state_service.get_amount_completed_instruments()
    assert res == 1


def test_get_amount_total_instruments(system_card: SystemCard):
    instrument_state_service = InstrumentStateService(system_card)
    _ = instrument_state_service.get_state_per_instrument()
    res = instrument_state_service.get_amount_total_instruments()
    assert res == 3


def test_get_amount_completed_instruments_one_completed(system_card: SystemCard):
    instrument_state_service = InstrumentStateService(system_card)
    _ = instrument_state_service.get_state_per_instrument()
    instrument_state_service.instrument_states = [{"in_progress": 0}, {"in_progress": 1}]
    res = instrument_state_service.get_amount_completed_instruments()
    assert res == 1
