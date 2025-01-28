import logging
from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from amt.models.user import User
from amt.repositories.users import UsersRepository

logger = logging.getLogger(__name__)


class UsersService:
    def __init__(
        self,
        repository: Annotated[UsersRepository, Depends(UsersRepository)],
    ) -> None:
        self.repository = repository
        self.cache: dict[UUID, User | None] = {}

    async def create_or_update(self, user: User) -> User:
        return await self.repository.upsert(user)

    async def find_by_id(self, id: UUID | str) -> User | None:
        id = UUID(id) if isinstance(id, str) else id
        if id not in self.cache:
            new_user = await self.repository.find_by_id(id)
            self.cache[id] = new_user
        return self.cache[id]

    async def find_all(
        self,
        search: str | None = None,
        sort: dict[str, str] | None = None,
        filters: dict[str, str | list[str | int]] | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Sequence[User]:
        return await self.repository.find_all(search, sort, filters, skip, limit)
