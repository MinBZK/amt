import logging
from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import lazyload
from sqlalchemy_utils import escape_like  # pyright: ignore[reportMissingTypeStubs, reportUnknownVariableType]

from amt.core.exceptions import AMTRepositoryError
from amt.models import User
from amt.repositories.deps import get_session

logger = logging.getLogger(__name__)


class UsersRepository:
    """
    The UsersRepository provides access to the repository layer.
    """

    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]) -> None:
        self.session = session

    async def find_all(self, search: str | None = None, limit: int | None = None) -> Sequence[User]:
        statement = select(User)
        if search:
            statement = statement.filter(User.name.ilike(f"%{escape_like(search)}%"))
        # https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#lazy-loading
        statement = statement.options(lazyload(User.organizations))
        if limit:
            statement = statement.limit(limit)

        return (await self.session.execute(statement)).scalars().all()

    async def find_by_id(self, id: UUID) -> User | None:
        """
        Returns the user with the given id.
        :param id: the id of the user to find
        :return: the user with the given id or an exception if no user was found
        """
        statement = select(User).where(User.id == id)
        # https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#lazy-loading
        statement = statement.options(lazyload(User.organizations))
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
                existing_user.email = user.email
                existing_user.email_hash = user.email_hash
                existing_user.name_encoded = user.name_encoded
                self.session.add(existing_user)
            else:
                self.session.add(user)
            await self.session.commit()
        except SQLAlchemyError as e:  # pragma: no cover
            logger.exception("Error saving user")
            await self.session.rollback()
            raise AMTRepositoryError from e

        return user
