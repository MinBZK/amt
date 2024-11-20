import asyncio
import logging
from collections.abc import Sequence
from typing import Any

from amt.clients.clients import TaskRegistryAPIClient, TaskType
from amt.core.exceptions import AMTNotFound

logger = logging.getLogger(__name__)


class TaskRegistryRepository:
    """
    Responsible for fetching tasks (instruments, measures, etc.) from the Task Registry API.
    """

    def __init__(self, client: TaskRegistryAPIClient) -> None:
        self.client = client

    async def fetch_tasks(self, task_type: TaskType, urns: str | Sequence[str] | None = None) -> list[dict[str, Any]]:
        """
        Fetches tasks (instruments, measures, etc.) with the given URNs.

        If urns contains an URN that is not a valid URN of a task, it is simply ignored.

        @param task_type: The type of task to fetch (e.g. TaskType.INSTRUMENTS, TaskType.MEASURES).
        @param urns: URNs of tasks to fetch. If None, function returns all tasks of the given type.
        @return: List of task data dictionaries with the given URNs in 'urns'.
        """
        if urns is None:
            all_valid_urns: list[str] = await self._fetch_valid_urns(task_type)
            return await self._fetch_tasks_by_urns(task_type, all_valid_urns)

        if isinstance(urns, str):
            urns = [urns]

        return await self._fetch_tasks_by_urns(task_type, urns)

    async def _fetch_valid_urns(self, task_type: TaskType) -> list[str]:
        """
        Fetches all valid URNs for the given task type.
        """
        content_list = await self.client.get_list_of_task(task_type)
        return [content.urn for content in content_list.root]

    async def _fetch_tasks_by_urns(self, task_type: TaskType, urns: Sequence[str]) -> list[dict[str, Any]]:
        """
        Fetches tasks given a list of URN's.
        If an URN is not valid, it is ignored.
        """
        get_tasks = [self.client.get_task_by_urn(task_type, urn) for urn in urns]
        results = await asyncio.gather(*get_tasks, return_exceptions=True)

        tasks: list[dict[str, Any]] = []
        failed_urns: list[str] = []
        for urn, result in zip(urns, results, strict=True):
            if isinstance(result, dict):
                tasks.append(result)
            elif isinstance(result, AMTNotFound):
                failed_urns.append(urn)
            elif isinstance(result, Exception):
                raise result

        if failed_urns:
            # Sonar cloud does not like displaying the failed urns, so  the warning is now
            # generic without specification of the urns.
            logger.warning("Cannot find all tasks")

        return tasks
