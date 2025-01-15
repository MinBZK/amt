import logging
from collections.abc import Sequence

from amt.clients.clients import TaskType, task_registry_api_client
from amt.repositories.task_registry import TaskRegistryRepository
from amt.schema.measure import Measure

logger = logging.getLogger(__name__)


class MeasuresService:
    def __init__(self, repository: TaskRegistryRepository) -> None:
        self.repository = repository

    async def fetch_measures(self, urns: str | Sequence[str] | None = None) -> list[Measure]:
        """
        Fetches measures with the given URNs.
        If urns contains an URN that is not a valid URN of an measure, it is simply ignored.
        @param urns: URNs of instruments to fetch. If None, function returns all measures.
        @return: List of measures with the given URNs in 'urns'.
        """
        task_data = await self.repository.fetch_tasks(TaskType.MEASURES, urns)
        return [Measure(**data) for data in task_data]


def create_measures_service() -> MeasuresService:
    repository = TaskRegistryRepository(task_registry_api_client)
    return MeasuresService(repository)
