import logging
from collections.abc import Sequence

from amt.clients.clients import TaskRegistryAPIClient, TaskType
from amt.repositories.task_registry import TaskRegistryRepository
from amt.schema.requirement import Requirement

logger = logging.getLogger(__name__)


class RequirementsService:
    def __init__(self, repository: TaskRegistryRepository) -> None:
        self.repository = repository

    async def fetch_requirements(self, urns: str | Sequence[str] | None = None) -> list[Requirement]:
        """
        Fetches measures with the given URNs.
        If urns contains an URN that is not a valid URN of an measure, it is simply ignored.
        @param urns: URNs of instruments to fetch. If None, function returns all measures.
        @return: List of measures with the given URNs in 'urns'.
        """
        task_data = await self.repository.fetch_tasks(TaskType.REQUIREMENTS, urns)
        return [Requirement(**data) for data in task_data]


def create_requirements_service() -> RequirementsService:
    client = TaskRegistryAPIClient()
    repository = TaskRegistryRepository(client)
    return RequirementsService(repository)
