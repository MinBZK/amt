import logging
from typing import Annotated

from fastapi import Depends

from tad.repositories.statuses import StatusesRepository

logger = logging.getLogger(__name__)


class StatusesService:
    def __init__(self, repository: Annotated[StatusesRepository, Depends(StatusesRepository)]):
        self.repository = repository

    def get_status(self, status_id):
        return self.repository.find_by_id(status_id)

    def get_statuses(self) -> []:
        return self.repository.find_all()
