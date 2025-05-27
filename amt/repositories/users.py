import logging
from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy_utils import escape_like  # pyright: ignore[reportMissingTypeStubs, reportUnknownVariableType]
from typing_extensions import deprecated

from amt.core.exceptions import AMTRepositoryError
from amt.models import User
from amt.repositories.deps import AsyncSessionWithCommitFlag, get_session
from amt.repositories.repository_classes import BaseRepository

logger = logging.getLogger(__name__)


class UsersRepository(BaseRepository):
    """
    The UsersRepository provides access to the repository layer.
    """

    def __init__(self, session: Annotated[AsyncSessionWithCommitFlag, Depends(get_session)]) -> None:
        super().__init__(session)
        self.cache: dict[UUID, User | None] = {}

    @deprecated(
        "This method can only be used to find all users."
        "Use the authorizations service to get organization or algorithm users"
    )
    async def find_all(
        self,
        search: str | None = None,
        sort: dict[str, str] | None = None,
        filters: dict[str, str | list[str | int]] | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Sequence[User]:
        statement = select(User)
        if search:
            statement = statement.filter(User.name.ilike(f"%{escape_like(search)}%"))
        if sort:
            if "name" in sort and sort["name"] == "ascending":
                statement = statement.order_by(func.lower(User.name).asc())
            elif "name" in sort and sort["name"] == "descending":
                statement = statement.order_by(func.lower(User.name).desc())
        # https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#lazy-loading
        if skip:
            statement = statement.offset(skip)
        if limit:
            statement = statement.limit(limit)

        return (await self.session.execute(statement)).scalars().all()

    async def find_by_id(self, id: UUID | str) -> User | None:
        """
        Returns the user with the given id.
        :param id: the id of the user to find
        :return: the user with the given id or an exception if no user was found
        """
        id = UUID(id) if isinstance(id, str) else id
        if id not in self.cache:
            try:
                # only cache existing users
                statement = select(User).where(User.id == id)
                new_user = (await self.session.execute(statement)).scalars().one()
                self.cache[id] = new_user
            except NoResultFound:
                return None
        return self.cache[id]

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
            self.session.should_commit = True
        except SQLAlchemyError as e:  # pragma: no cover
            logger.exception("Error saving user")
            await self.session.rollback()
            raise AMTRepositoryError from e

        return user
