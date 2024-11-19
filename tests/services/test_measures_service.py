from typing import Any

import pytest
from amt.clients.clients import TaskType
from amt.repositories.task_registry import TaskRegistryRepository
from amt.schema.measure import Measure
from amt.services.measures import MeasuresService
from pytest_mock import MockerFixture, MockType


@pytest.fixture
def mock_repository(mocker: MockerFixture) -> MockType:
    return mocker.create_autospec(TaskRegistryRepository)


@pytest.fixture
def service(mock_repository: MockType) -> MeasuresService:
    return MeasuresService(repository=mock_repository)  # type: ignore


@pytest.fixture
def sample_data() -> list[dict[str, Any]]:
    return [
        {
            "urn": "urn:measure:1",
            "name": "Measure 1",
            "schema_version": "1.1.0",
            "description": "description_1",
            "links": [],
            "url": "url_1",
        },
        {
            "urn": "urn:measure:2",
            "name": "Measure 2",
            "schema_version": "1.1.0",
            "description": "description_2",
            "url": "url_2",
            "language": "nl",
        },
    ]


@pytest.mark.asyncio
async def test_fetch_all_measures(
    service: MeasuresService, mock_repository: MockType, sample_data: list[dict[str, Any]]
):
    # given
    mock_repository.fetch_tasks.return_value = sample_data

    # when
    result = await service.fetch_measures()

    # then
    mock_repository.fetch_tasks.assert_called_once_with(TaskType.MEASURES, None)

    assert len(result) == 2
    assert all(isinstance(task, Measure) for task in result)


@pytest.mark.asyncio
async def test_fetch_measures_with_single_urn(
    service: MeasuresService, mock_repository: MockType, sample_data: list[dict[str, Any]], mocker: MockerFixture
) -> None:
    # given
    single_urn: str = "urn:measure:1"
    mock_data = [sample_data[0]]
    mock_repository.fetch_tasks.return_value = mock_data

    # when
    result = await service.fetch_measures(single_urn)

    # then
    mock_repository.fetch_tasks.assert_called_once_with(TaskType.MEASURES, single_urn)
    assert len(result) == 1
    assert isinstance(result[0], Measure)
    assert result[0].urn == "urn:measure:1"


@pytest.mark.asyncio
async def test_fetch_measures_with_specific_urns(
    service: MeasuresService, mock_repository: MockType, sample_data: list[dict[str, Any]], mocker: MockerFixture
) -> None:
    # given
    urns = ["urn:measure:1", "urn:measure:2"]
    mock_repository.fetch_tasks.return_value = sample_data

    # when
    result = await service.fetch_measures(urns)

    # then
    mock_repository.fetch_tasks.assert_called_once_with(TaskType.MEASURES, urns)
    assert len(result) == 2
    assert all(isinstance(task, Measure) for task in result)
    assert result[0].urn == "urn:measure:1"
    assert result[1].urn == "urn:measure:2"


@pytest.mark.asyncio
async def test_fetch_measures_with_empty_result(
    service: MeasuresService, mock_repository: MockType, mocker: MockerFixture
) -> None:
    # given
    mock_repository.fetch_tasks.return_value = []

    # when
    result = await service.fetch_measures(["non_existent_urn"])

    # then
    assert len(result) == 0
    mock_repository.fetch_tasks.assert_called_once_with(TaskType.MEASURES, ["non_existent_urn"])
