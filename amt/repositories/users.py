import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from amt.core.exceptions import AMTRepositoryError
from amt.models.user import User
from amt.repositories.deps import get_session

logger = logging.getLogger(__name__)


class UsersRepository:
    """
    The UsersRepository provides access to the repository layer.
    """

    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]) -> None:
        self.session = session

    async def find_by_id(self, id: UUID) -> User | None:
        """
        Returns the user with the given id.
        :param id: the id of the user to find
        :return: the user with the given id or an exception if no user was found
        """
        statement = select(User).where(User.id == id)
        try:
            return (await self.session.execute(statement)).scalars().one()
        except NoResultFound:
            return None

    async def upsert(self, user: User) -> User:
        """
        Upserts (create or update) a user.
        :param user: the user to upsert.
        :return: the upserted user.
        """
        try:
            existing_user = await self.find_by_id(user.id)
            if existing_user:
                existing_user.name = user.name
            else:
                self.session.add(user)
            await self.session.commit()
        except SQLAlchemyError as e:  # pragma: no cover
            logger.exception("Error saving user")
            await self.session.rollback()
            raise AMTRepositoryError from e

        return user
