from typing import Any

import pytest
from amt.clients.clients import TaskType
from amt.repositories.task_registry import TaskRegistryRepository
from amt.schema.instrument import Instrument
from amt.services.instruments import InstrumentsService
from pytest_mock import MockerFixture, MockType


@pytest.fixture
def mock_repository(mocker: MockerFixture) -> MockType:
    return mocker.create_autospec(TaskRegistryRepository)


@pytest.fixture
def service(mock_repository: MockType) -> InstrumentsService:
    return InstrumentsService(repository=mock_repository)  # type: ignore


@pytest.fixture
def sample_data() -> list[dict[str, Any]]:
    return [
        {
            "urn": "urn:instrument:1",
            "name": "Instrument 1",
            "description": "description_1",
            "url": "url_1",
            "language": "nl",
            "date": "",
            "owners": [],
        },
        {
            "urn": "urn:instrument:2",
            "name": "Instrument 2",
            "description": "description_2",
            "url": "url_2",
            "language": "nl",
            "date": "",
            "owners": [],
        },
    ]


@pytest.mark.asyncio
async def test_fetch_all_instruments(
    service: InstrumentsService, mock_repository: MockType, sample_data: list[dict[str, Any]]
):
    # given
    mock_repository.fetch_tasks.return_value = sample_data

    # when
    result = await service.fetch_instruments()

    # then
    mock_repository.fetch_tasks.assert_called_once_with(TaskType.INSTRUMENTS, None)

    assert len(result) == 2
    assert all(isinstance(instrument, Instrument) for instrument in result)


@pytest.mark.asyncio
async def test_fetch_instruments_with_single_urn(
    service: InstrumentsService, mock_repository: MockType, sample_data: list[dict[str, Any]], mocker: MockerFixture
) -> None:
    # given
    single_urn: str = "urn:instrument:1"
    mock_data = [sample_data[0]]
    mock_repository.fetch_tasks.return_value = mock_data

    # when
    result = await service.fetch_instruments(single_urn)

    # then
    mock_repository.fetch_tasks.assert_called_once_with(TaskType.INSTRUMENTS, single_urn)
    assert len(result) == 1
    assert isinstance(result[0], Instrument)
    assert result[0].urn == "urn:instrument:1"


@pytest.mark.asyncio
async def test_fetch_instruments_with_specific_urns(
    service: InstrumentsService, mock_repository: MockType, sample_data: list[dict[str, Any]], mocker: MockerFixture
) -> None:
    # given
    urns = ["urn:instrument:1", "urn:instrument:2"]
    mock_repository.fetch_tasks.return_value = sample_data

    # when
    result = await service.fetch_instruments(urns)

    # then
    mock_repository.fetch_tasks.assert_called_once_with(TaskType.INSTRUMENTS, urns)
    assert len(result) == 2
    assert all(isinstance(instrument, Instrument) for instrument in result)
    assert result[0].urn == "urn:instrument:1"
    assert result[1].urn == "urn:instrument:2"


@pytest.mark.asyncio
async def test_fetch_instruments_with_empty_result(
    service: InstrumentsService, mock_repository: MockType, mocker: MockerFixture
) -> None:
    # given
    mock_repository.fetch_tasks.return_value = []

    # when
    result = await service.fetch_instruments(["non_existent_urn"])

    # then
    assert len(result) == 0
    mock_repository.fetch_tasks.assert_called_once_with(TaskType.INSTRUMENTS, ["non_existent_urn"])
