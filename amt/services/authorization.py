import contextlib
from typing import Any
from uuid import UUID

from amt.core.authorization import AuthorizationType, AuthorizationVerb
from amt.repositories.authorizations import AuthorizationRepository
from amt.schema.permission import Permission

PermissionTuple = tuple[str, list[AuthorizationVerb], str, int]
PermissionsList = list[PermissionTuple]


class AuthorizationService:
    def __init__(self) -> None:
        self.repository = AuthorizationRepository()

    async def find_by_user(self, user: dict[str, Any] | None) -> dict[str, list[AuthorizationVerb]]:
        if not user:
            return {}
        else:
            permissions: dict[str, list[AuthorizationVerb]] = {}

            uuid = UUID(user["sub"])
            authorizations: PermissionsList = await self.repository.find_by_user(uuid)  # type: ignore
            for auth in authorizations:
                auth_dict: dict[str, int] = {"organization_id": -1, "algoritme_id": -1}

                if auth[2] == AuthorizationType.ORGANIZATION:
                    auth_dict["organization_id"] = auth[3]

                if auth[2] == AuthorizationType.ALGORITHM:
                    auth_dict["algoritme_id"] = auth[3]

                resource: str = auth[0]
                verbs: list[AuthorizationVerb] = auth[1]
                with contextlib.suppress(Exception):
                    resource = resource.format(**auth_dict)

                permission: Permission = Permission(resource=resource, verb=verbs)

                permissions.update({permission.resource: permission.verb})

            return permissions
