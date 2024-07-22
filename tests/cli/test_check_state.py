from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from click.testing import CliRunner
from tad.cli import check_state
from tad.cli.check_state import (
    get_all_next_tasks,
    get_first_lifecycle_idx,
    get_instrument_result_from_system_card,
    get_next_tasks_per_instrument,
    get_requested_instruments,
    get_task_timestamp_from_assessment_card,
    get_tasks_by_priority,
)
from tad.core.exceptions import InstrumentError
from tad.schema.assessment_card import AssessmentCard
from tad.schema.instrument import InstrumentTask
from tad.schema.system_card import SystemCard
from tad.services.instruments import InstrumentsService
from tad.services.storage import FileSystemStorageService, StorageFactory
from tests.constants import default_instrument
from yaml import YAMLError


@pytest.fixture()
def system_card_data() -> dict[str, Any]:
    return {
        "name": "test-system-card",
        "schema_version": "0.0.0",
        "selected_instruments": [],
        "assessments": [
            {
                "urn": "urn:instrument:assessment",
                "contents": [{"urn": "urn:instrument:assessment:task", "timestamp": "2024-04-17T12:03:23Z"}],
            }
        ],
    }


@pytest.fixture()
def system_card(system_card_data: dict[str, Any]) -> SystemCard:
    system_card = SystemCard(**system_card_data)
    return system_card


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


def test_get_system_card(system_card: SystemCard, system_card_data: dict[str, Any]):
    init_orig = StorageFactory.init

    storage_mock = Mock()
    storage_mock.read.return_value = system_card_data
    StorageFactory.init = Mock(return_value=storage_mock)

    assert system_card == check_state.get_system_card(Path("dummy"))

    StorageFactory.init = init_orig


def test_get_requested_instruments():
    instrument0 = default_instrument(urn="instrument0")
    instrument1 = default_instrument(urn="instrument1")
    instrument2 = default_instrument(urn="instrument2")
    all_instruments_cards = [instrument0, instrument1, instrument2]
    expected = {"instrument0": instrument0, "instrument2": instrument2}
    assert expected == get_requested_instruments(all_instruments_cards, ["instrument0", "instrument2"])


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


def test_cli(capsys: pytest.CaptureFixture[str], system_card: SystemCard):
    fetch_instruments_orig = InstrumentsService.fetch_instruments
    get_system_card_orig = check_state.get_system_card
    instrument = default_instrument(
        urn="urn:instrument:assessment",
        tasks=[
            InstrumentTask(question="question", urn="urn:instrument:assessment:task", lifecycle=["Ontwerp"]),
            InstrumentTask(question="question", urn="urn:instrument:assessment:task2", lifecycle=["Ontwerp"]),
        ],
    )

    return_value = [instrument]
    InstrumentsService.fetch_instruments = Mock(return_value=return_value)
    check_state.get_system_card = Mock(return_value=system_card)
    runner = CliRunner()
    # workaround for https://github.com/pallets/click/issues/824
    with capsys.disabled() as _:
        result = runner.invoke(get_tasks_by_priority, ["urn:instrument:assessment", "example/system_test_card.yaml"])  # type: ignore
        assert "urn:instrument:assessment:task2" in result.output
    InstrumentsService.fetch_instruments = fetch_instruments_orig
    check_state.get_system_card = get_system_card_orig


def test_cli_with_exception(capsys: pytest.CaptureFixture[str], system_card: SystemCard):
    fetch_instruments_orig = InstrumentsService.fetch_instruments
    InstrumentsService.fetch_instruments = Mock(side_effect=InstrumentError("Test error message"))
    runner = CliRunner()
    # workaround for https://github.com/pallets/click/issues/824
    with capsys.disabled() as _:
        result = runner.invoke(get_tasks_by_priority, ["urn:instrument:assessment", "example/system_test_card.yaml"])  # type: ignore
        assert "Test error message" in result.output
    InstrumentsService.fetch_instruments = fetch_instruments_orig


def test_cli_with_exception_yaml(capsys: pytest.CaptureFixture[str], system_card: SystemCard):
    read_orig = FileSystemStorageService.read
    FileSystemStorageService.read = Mock(side_effect=YAMLError("Test error message"))
    runner = CliRunner()
    # workaround for https://github.com/pallets/click/issues/824
    with capsys.disabled() as _:
        result = runner.invoke(get_tasks_by_priority, ["urn:instrument:assessment", "example/system_test_card.yaml"])  # type: ignore
        assert "Sorry, an error occurred; yaml could not be parsed:" in result.output
    FileSystemStorageService.read = read_orig
