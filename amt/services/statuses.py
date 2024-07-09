import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends

from amt.models import Status
from amt.repositories.statuses import StatusesRepository

logger = logging.getLogger(__name__)


class StatusesService:
    def __init__(self, repository: Annotated[StatusesRepository, Depends(StatusesRepository)]) -> None:
        self.repository = repository

    def get_status(self, status_id: int) -> Status:
        return self.repository.find_by_id(status_id)

    def get_statuses(self) -> Sequence[Status]:
        return self.repository.find_all()
