import logging
from collections.abc import Sequence

from amt.clients.clients import TaskType, task_registry_api_client
from amt.repositories.task_registry import TaskRegistryRepository
from amt.schema.instrument import Instrument

logger = logging.getLogger(__name__)


class InstrumentsService:
    def __init__(self, repository: TaskRegistryRepository) -> None:
        self.repository = repository

    async def fetch_instruments(self, urns: str | Sequence[str] | None = None) -> list[Instrument]:
        """
        Fetches instruments with the given URNs.
        If urns contains an URN that is not a valid URN of an instrument, it is simply ignored.
        @param urns: URNs of instruments to fetch. If None, function returns all instruments.
        @return: List of instruments with the given URNs in 'urns'.
        """
        task_data = await self.repository.fetch_tasks(TaskType.INSTRUMENTS, urns)
        return [Instrument(**data) for data in task_data]


def create_instrument_service() -> InstrumentsService:
    repository = TaskRegistryRepository(task_registry_api_client)
    return InstrumentsService(repository)
