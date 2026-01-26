import logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from amt.core.exceptions import AMTRepositoryError
from amt.models import Publication
from amt.repositories.deps import AsyncSessionWithCommitFlag, get_session
from amt.repositories.repository_classes import BaseRepository

logger = logging.getLogger(__name__)


class PublicationsRepository(BaseRepository):
    def __init__(self, session: Annotated[AsyncSessionWithCommitFlag, Depends(get_session)]) -> None:
        super().__init__(session)

    async def find_by_id(self, publication_id: int) -> Publication:
        try:
            statement = select(Publication).where(Publication.id == publication_id)
            result = await self.session.execute(statement)
            return result.scalars().one()
        except NoResultFound as e:
            logger.exception("Publication not found")
            raise AMTRepositoryError from e

    async def find_by_algorithm_id(self, algorithm_id: int) -> Publication | None:
        try:
            statement = select(Publication).where(Publication.algorithm_id == algorithm_id)
            result = await self.session.execute(statement)
            return result.scalars().one_or_none()
        except Exception as e:
            logger.exception("Error finding publication by algorithm_id")
            raise AMTRepositoryError from e

    async def delete_by_algorithm_id(self, algorithm_id: int) -> None:
        try:
            result = await self.find_by_algorithm_id(algorithm_id)
            if result:
                await self.session.delete(result)
                await self.session.flush()
                self.session.should_commit = True
        except Exception as e:
            logger.exception("Error finding publication by algorithm_id")
            raise AMTRepositoryError from e

    async def save(self, publication: Publication) -> Publication:
        self.session.add(publication)
        await self.session.flush()
        self.session.should_commit = True
        return publication
