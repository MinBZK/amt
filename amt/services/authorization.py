from typing import Any
from uuid import UUID

# from amt.core.authorization import AuthorizationType
from amt.repositories.authorizations import AuthorizationRepository

# from amt.schema.permission import Permission


class AuthorizationService:
    def __init__(self) -> None:
        self.repository = AuthorizationRepository()

    async def find_by_user(self, user: dict[str, Any] | None) -> dict[str, list[str]]:
        if not user:
            return {}
        else:
            permissions: dict[str, list[str]] = {}

            authorizations = await self.repository.find_by_user(UUID(user["sub"]))
            for auth in authorizations:
                pass

            return permissions
