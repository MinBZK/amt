import logging
from enum import StrEnum
from typing import Any

import httpx
from amt.core.exceptions import AMTInstrumentError, AMTNotFound
from amt.schema.github import RepositoryContent
from async_lru import alru_cache

logger = logging.getLogger(__name__)


class TaskType(StrEnum):
    INSTRUMENTS = "instruments"
    REQUIREMENTS = "requirements"
    MEASURES = "measures"


class APIClient:
    """
    Base API client with common HTTP functionality.
    """

    def __init__(self, base_url: str, max_retries: int = 3, timeout: int = 5) -> None:
        self.base_url = base_url
        transport = httpx.AsyncHTTPTransport(retries=max_retries)
        self.client = httpx.AsyncClient(timeout=timeout, transport=transport)

    async def _make_request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self.client.get(f"{self.base_url}/{endpoint}", params=params)
        if response.status_code != 200:
            raise AMTNotFound()
        return response.json()


class TaskRegistryAPIClient(APIClient):
    """
    Client for interacting with the Task Registry API.
    """

    def __init__(self, max_retries: int = 3, timeout: int = 5) -> None:
        super().__init__(
            base_url="https://task-registry.apps.digilab.network", max_retries=max_retries, timeout=timeout
        )

    async def get_list_of_task(self, task: TaskType = TaskType.INSTRUMENTS) -> RepositoryContent:
        response_data = await self._make_request(f"{task.value}/")
        return RepositoryContent.model_validate(response_data["entries"])

    async def get_task_by_urn(self, task_type: TaskType, urn: str, version: str = "latest") -> dict[str, Any]:
        response_data = await self._make_request(f"{task_type.value}/urn/{urn}", params={"version": version})
        if "urn" not in response_data:
            logger.exception(f"Invalid task {task_type.value} fetched: key 'urn' must occur in task {task_type.value}.")
            raise AMTInstrumentError()
        return response_data


@alru_cache
async def get_task_by_urn(task_type: TaskType, urn: str, version: str = "latest") -> dict[str, Any]:
    client = TaskRegistryAPIClient()
    return await client.get_task_by_urn(task_type, urn, version)
