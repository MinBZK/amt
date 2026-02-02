import logging
from typing import Annotated

from fastapi import Depends

from amt.models import Publication
from amt.repositories.publications import PublicationsRepository
from amt.services.service_classes import BaseService

logger = logging.getLogger(__name__)


class PublicationsService(BaseService):
    def __init__(
        self,
        repository: Annotated[PublicationsRepository, Depends(PublicationsRepository)],
    ) -> None:
        self.repository = repository

    async def get(self, publication_id: int) -> Publication:
        return await self.repository.find_by_id(publication_id)

    async def get_by_algorithm_id(self, algorithm_id: int) -> Publication | None:
        return await self.repository.find_by_algorithm_id(algorithm_id)

    async def delete_by_algorithm_id(self, algorithm_id: int) -> None:
        return await self.repository.delete_by_algorithm_id(algorithm_id)

    async def update(self, publication: Publication) -> Publication:
        publication = await self.repository.save(publication)
        return publication
