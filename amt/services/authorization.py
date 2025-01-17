from typing import Any
from uuid import UUID

from amt.api.utils import SafeDict
from amt.core.authorization import AuthorizationType, AuthorizationVerb
from amt.models import User
from amt.repositories.authorizations import AuthorizationRepository
from amt.schema.permission import Permission

PermissionTuple = tuple[str, list[AuthorizationVerb], str, int]
PermissionsList = list[PermissionTuple]


class AuthorizationService:
    def __init__(self) -> None:
        self.repository = AuthorizationRepository()

    async def get_user(self, user_id: UUID) -> User | None:
        return await self.repository.get_user(user_id)

    async def find_by_user(self, user: dict[str, Any] | None) -> dict[str, list[AuthorizationVerb]]:
        if not user:
            return {}
        else:
            permissions: dict[str, list[AuthorizationVerb]] = {}

            uuid = UUID(user["sub"])
            authorizations: PermissionsList = await self.repository.find_by_user(uuid)  # type: ignore
            for auth in authorizations:
                auth_dict: dict[str, int | str] = {}

                if auth[2] == AuthorizationType.ORGANIZATION:
                    # TODO: check the path if we need the slug or the id?
                    auth_dict["organization_id"] = auth[3]
                    auth_dict["organization_slug"] = auth[3]

                if auth[2] == AuthorizationType.ALGORITHM:
                    auth_dict["algorithm_id"] = auth[3]

                resource: str = auth[0]
                verbs: list[AuthorizationVerb] = auth[1]

                resource = resource.format_map(SafeDict(auth_dict))

                permission: Permission = Permission(resource=resource, verb=verbs)

                permissions.update({permission.resource: permission.verb})

            return permissions
