from typing import Any

import pytest
from amt.clients.clients import TaskType
from amt.repositories.task_registry import TaskRegistryRepository
from amt.schema.requirement import Requirement
from amt.services.requirements import RequirementsService
from pytest_mock import MockerFixture, MockType


@pytest.fixture
def mock_repository(mocker: MockerFixture) -> MockType:
    return mocker.create_autospec(TaskRegistryRepository)


@pytest.fixture
def service(mock_repository: MockType) -> RequirementsService:
    return RequirementsService(repository=mock_repository)  # type: ignore


@pytest.fixture
def sample_data() -> list[dict[str, Any]]:
    return [
        {
            "urn": "urn:requirement:1",
            "name": "Requirement 1",
            "description": "description_1",
            "schema_version": "1.1.0",
            "links": [],
            "always_applicable": 1,
            "ai_act_profile": [],
        },
        {
            "urn": "urn:requirement:2",
            "name": "Requirement 2",
            "description": "description_2",
            "schema_version": "1.1.0",
            "url": "url_2",
            "always_applicable": 1,
            "ai_act_profile": [],
        },
    ]


@pytest.mark.asyncio
async def test_fetch_all_requirements(
    service: RequirementsService, mock_repository: MockType, sample_data: list[dict[str, Any]]
):
    # given
    mock_repository.fetch_tasks.return_value = sample_data

    # when
    result = await service.fetch_requirements()

    # then
    mock_repository.fetch_tasks.assert_called_once_with(TaskType.REQUIREMENTS, None)

    assert len(result) == 2
    assert all(isinstance(task, Requirement) for task in result)


@pytest.mark.asyncio
async def test_fetch_requirements_with_single_urn(
    service: RequirementsService, mock_repository: MockType, sample_data: list[dict[str, Any]], mocker: MockerFixture
) -> None:
    # given
    single_urn: str = "urn:requirement:1"
    mock_data = [sample_data[0]]
    mock_repository.fetch_tasks.return_value = mock_data

    # when
    result = await service.fetch_requirements(single_urn)

    # then
    mock_repository.fetch_tasks.assert_called_once_with(TaskType.REQUIREMENTS, single_urn)
    assert len(result) == 1
    assert isinstance(result[0], Requirement)
    assert result[0].urn == "urn:requirement:1"


@pytest.mark.asyncio
async def test_fetch_requirements_with_specific_urns(
    service: RequirementsService, mock_repository: MockType, sample_data: list[dict[str, Any]], mocker: MockerFixture
) -> None:
    # given
    urns = ["urn:requirement:1", "urn:requirement:2"]
    mock_repository.fetch_tasks.return_value = sample_data

    # when
    result = await service.fetch_requirements(urns)

    # then
    mock_repository.fetch_tasks.assert_called_once_with(TaskType.REQUIREMENTS, urns)
    assert len(result) == 2
    assert all(isinstance(task, Requirement) for task in result)
    assert result[0].urn == "urn:requirement:1"
    assert result[1].urn == "urn:requirement:2"


@pytest.mark.asyncio
async def test_fetch_requirements_with_empty_result(
    service: RequirementsService, mock_repository: MockType, mocker: MockerFixture
) -> None:
    # given
    mock_repository.fetch_tasks.return_value = []

    # when
    result = await service.fetch_requirements(["non_existent_urn"])

    # then
    assert len(result) == 0
    mock_repository.fetch_tasks.assert_called_once_with(TaskType.REQUIREMENTS, ["non_existent_urn"])
