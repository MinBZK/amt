import logging

from tad.repositories.statuses import StatusesRepository

logger = logging.getLogger(__name__)


class StatusesService:
    @staticmethod
    def get_status(status_id):
        return StatusesRepository.find_by_id(status_id)

    @staticmethod
    def get_statuses() -> []:
        return StatusesRepository.find_all()
