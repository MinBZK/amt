import json

import pytest
from amt.clients.clients import TaskRegistryAPIClient, TaskType
from amt.core.exceptions import AMTNotFound
from amt.schema.github import RepositoryContent
from pytest_httpx import HTTPXMock
from tests.constants import TASK_REGISTRY_CONTENT_PAYLOAD, TASK_REGISTRY_LIST_PAYLOAD


@pytest.mark.asyncio
async def test_task_registry_api_client_get_instrument_list(httpx_mock: HTTPXMock):
    task_registry_api_client = TaskRegistryAPIClient()
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/", content=TASK_REGISTRY_LIST_PAYLOAD.encode()
    )

    result = await task_registry_api_client.get_list_of_task(task=TaskType.INSTRUMENTS)

    assert result == RepositoryContent.model_validate(json.loads(TASK_REGISTRY_LIST_PAYLOAD)["entries"])


@pytest.mark.asyncio
async def test_task_registry_api_client_get_instrument_list_not_succesfull(httpx_mock: HTTPXMock):
    task_registry_api_client = TaskRegistryAPIClient()
    httpx_mock.add_response(status_code=408, url="https://task-registry.apps.digilab.network/instruments/")

    # then
    with pytest.raises(AMTNotFound):
        await task_registry_api_client.get_list_of_task()


@pytest.mark.asyncio
async def test_task_registry_api_client_get_instrument(httpx_mock: HTTPXMock):
    # given
    task_registry_api_client = TaskRegistryAPIClient()
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/urn/urn:nl:aivt:tr:iama:1.0?version=latest",
        content=TASK_REGISTRY_CONTENT_PAYLOAD.encode(),
    )

    # when
    urn = "urn:nl:aivt:tr:iama:1.0"
    result = await task_registry_api_client.get_task_by_urn(TaskType.INSTRUMENTS, urn)

    # then
    assert result == json.loads(TASK_REGISTRY_CONTENT_PAYLOAD)


@pytest.mark.asyncio
async def test_task_registry_api_client_get_instrument_not_succesfull(httpx_mock: HTTPXMock):
    task_registry_api_client = TaskRegistryAPIClient()
    httpx_mock.add_response(
        status_code=408,
        url="https://task-registry.apps.digilab.network/instruments/urn/urn:nl:aivt:tr:iama:1.0?version=latest",
    )

    urn = "urn:nl:aivt:tr:iama:1.0"

    # then
    with pytest.raises(AMTNotFound):
        await task_registry_api_client.get_task_by_urn(TaskType.INSTRUMENTS, urn)
