# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportAttributeAccessIssue=false
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import amt.services.instruments_and_requirements_state
import pytest
from amt.cli.check_state import get_requested_instruments, get_tasks_by_priority
from amt.core.exceptions import AMTInstrumentError
from amt.schema.instrument import InstrumentTask
from amt.schema.system_card import SystemCard
from amt.services.instruments import InstrumentsService
from amt.services.storage import FileSystemStorageService, StorageFactory
from click.testing import CliRunner
from tests.constants import default_instrument
from yaml import YAMLError


@pytest.fixture
def system_card_data() -> dict[str, Any]:
    return {
        "name": "test-system-card",
        "schema_version": "0.0.0",
        "instruments": [],
        "assessments": [
            {
                "urn": "urn:instrument:assessment",
                "contents": [{"urn": "urn:instrument:assessment:task", "timestamp": "2024-04-17T12:03:23Z"}],
            }
        ],
    }


@pytest.fixture
def system_card(system_card_data: dict[str, Any]) -> SystemCard:
    system_card = SystemCard(**system_card_data)
    return system_card


def test_get_system_card(system_card: SystemCard, system_card_data: dict[str, Any], mocker):
    mocker.patch('amt.services.storage.StorageFactory.init', return_value=mocker.Mock(read=mocker.Mock(return_value=system_card_data)))
    assert system_card == amt.cli.check_state.get_system_card(Path("dummy"))

def test_get_requested_instruments():
    instrument0 = default_instrument(urn="instrument0")
    instrument1 = default_instrument(urn="instrument1")
    instrument2 = default_instrument(urn="instrument2")
    all_instruments_cards = [instrument0, instrument1, instrument2]
    expected = {"instrument0": instrument0, "instrument2": instrument2}
    assert expected == get_requested_instruments(all_instruments_cards, ["instrument0", "instrument2"])


def test_cli(capsys: pytest.CaptureFixture[str], system_card: SystemCard, mocker):
    instrument = default_instrument(
        urn="urn:instrument:assessment",
        tasks=[
            InstrumentTask(question="question", urn="urn:instrument:assessment:task", lifecycle=["Ontwerp"]),
            InstrumentTask(question="question", urn="urn:instrument:assessment:task2", lifecycle=["Ontwerp"]),
        ],
    )

    mocker.patch('amt.services.instruments.InstrumentsService.fetch_instruments' , return_value=[instrument])
    mocker.patch('amt.cli.check_state.get_system_card', return_value=system_card)
    runner = CliRunner()
    # workaround for https://github.com/pallets/click/issues/824
    with capsys.disabled() as _:
        result = runner.invoke(get_tasks_by_priority, ["urn:instrument:assessment", "example/system_test_card.yaml"])  # type: ignore
        assert "urn:instrument:assessment:task2" in result.output


def test_cli_with_exception(capsys: pytest.CaptureFixture[str], system_card: SystemCard, mocker):
    mocker.patch('amt.services.instruments.InstrumentsService.fetch_instruments', side_effect=AMTInstrumentError())
    runner = CliRunner()
    # workaround for https://github.com/pallets/click/issues/824
    with capsys.disabled() as _:
        result = runner.invoke(get_tasks_by_priority, ["urn:instrument:assessment", "example/system_test_card.yaml"])  # type: ignore
        assert "Sorry, an error occurred" in result.output


def test_cli_with_exception_yaml(capsys: pytest.CaptureFixture[str], system_card: SystemCard, mocker):
    mocker.patch('amt.services.storage.FileSystemStorageService.read' , side_effect=YAMLError("Test error message"))
    runner = CliRunner()
    # workaround for https://github.com/pallets/click/issues/824
    with capsys.disabled() as _:
        result = runner.invoke(get_tasks_by_priority, ["urn:instrument:assessment", "example/system_test_card.yaml"])  # type: ignore
        assert "Sorry, an error occurred; yaml could not be parsed:" in result.output
