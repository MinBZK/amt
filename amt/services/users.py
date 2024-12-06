import logging
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

    async def get(self, id: str | UUID) -> User | None:
        id = UUID(id) if isinstance(id, str) else id
        return await self.repository.find_by_id(id)

    async def create_or_update(self, user: User) -> User:
        return await self.repository.upsert(user)

    async def find_by_id(self, id: UUID | str) -> User | None:
        return await self.repository.find_by_id(id)
