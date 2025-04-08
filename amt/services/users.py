import logging
from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from typing_extensions import deprecated

from amt.models.user import User
from amt.repositories.users import UsersRepository
from amt.services.service_classes import BaseService

logger = logging.getLogger(__name__)


class UsersService(BaseService):
    def __init__(
        self,
        repository: Annotated[UsersRepository, Depends(UsersRepository)],
    ) -> None:
        self.repository = repository

    async def create_or_update(self, user: User) -> User:
        return await self.repository.upsert(user)

    async def find_by_id(self, id: UUID | str) -> User | None:
        id = UUID(id) if isinstance(id, str) else id
        return await self.repository.find_by_id(id)

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
        return await self.repository.find_all(search, sort, filters, skip, limit)  # pyright: ignore[reportDeprecated]
