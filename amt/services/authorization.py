from collections.abc import Sequence
from typing import Annotated, Any
from uuid import UUID

from async_lru import alru_cache
from fastapi import Depends

from amt.api.utils import SafeDict
from amt.core.authorization import AuthorizationType, AuthorizationVerb
from amt.models import Algorithm, Authorization, Organization, Role, User
from amt.models.base import Base
from amt.repositories.algorithms import AlgorithmsRepository
from amt.repositories.authorizations import AuthorizationRepository, PermissionsList
from amt.repositories.organizations import OrganizationsRepository
from amt.schema.permission import Permission
from amt.services.service_classes import BaseService


class AuthorizationsService(BaseService):
    def __init__(
        self,
        repository: Annotated[AuthorizationRepository, Depends(AuthorizationRepository)],
        organizations_repository: Annotated[OrganizationsRepository, Depends(OrganizationsRepository)],
        algorithms_repository: Annotated[AlgorithmsRepository, Depends(AlgorithmsRepository)],
    ) -> None:
        self.repository = repository
        self.organizations_repository = organizations_repository
        self.algorithms_repository = algorithms_repository

    async def get_user(self, user_id: UUID) -> User | None:
        return await self.repository.get_user(user_id)

    async def find_by_user(self, user: dict[str, Any] | None) -> dict[str, list[AuthorizationVerb]]:
        if not user:
            return {}
        else:
            permissions: dict[str, list[AuthorizationVerb]] = {}

            uuid = UUID(user["sub"])
            authorizations: PermissionsList = await self.repository.find_by_user(uuid)
            authorizations += AuthorizationRepository.get_default_permissions()
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

    async def add_role_for_user(
        self, user_id: UUID | str, role_id: int, role_type: AuthorizationType, type_id: int
    ) -> None:
        await self.repository.add_role_for_user(user_id, role_id, role_type, type_id)

    async def get_by_id(self, authorization_id: int) -> Authorization | None:
        return await self.repository.get_by_id(authorization_id)

    async def get_users_with_authorizations(
        self,
        type_id: int,
        authorization_type: AuthorizationType,
        search: str | None = None,
        sort: dict[str, str] | None = None,
        filters: dict[str, str | list[str | int]] | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> list[tuple[User, Authorization, Role]]:
        return await self.repository.get_users_with_authorizations(
            type_id, authorization_type, search, sort, filters, skip, limit
        )

    @alru_cache
    async def get_role_by_id(self, role_id: int) -> Role | None:
        return await self.repository.get_role_by_id(role_id)

    @alru_cache
    async def get_role(self, role_name: str) -> Role:
        return await self.repository.get_role(role_name)

    async def update(self, authorization: Authorization) -> Authorization:
        return await self.repository.save(authorization)

    async def find_all(
        self,
        search: str | None = None,
        sort: dict[str, str] | None = None,
        filters: dict[str, str | int | list[str | int]] | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> list[tuple[User, Authorization, Role, type[Base] | None]]:
        return await self.repository.find_all(search, sort, filters, skip, limit)

    async def remove_algorithm_roles(self, user_id: str | UUID, algorithm: Algorithm | list[Algorithm]) -> None:
        await self.repository.remove_algorithm_roles(user_id, algorithm)

    async def remove_all_roles(self, user_id: str | UUID, organization: Organization) -> None:
        await self.repository.remove_all_roles(user_id, organization)

    async def add_authorization(
        self, user_id: str | UUID, type_id: int, authorization_type: AuthorizationType, role_id: int
    ) -> Authorization:
        user_id = UUID(user_id) if isinstance(user_id, str) else user_id
        authorization = Authorization(
            user_id=user_id,
            type_id=type_id,
            type=authorization_type,
            role_id=role_id,
        )
        return await self.repository.save(authorization)

    async def find_all_by_user_and_type(
        self, user_id: str | UUID, authorization_type: AuthorizationType
    ) -> Sequence[Authorization]:
        return await self.repository.find_all_by_user_and_type(user_id, authorization_type)

    async def find_by_user_and_type(
        self, user_id: str | UUID, type_id: int, authorization_type: AuthorizationType
    ) -> Authorization:
        return await self.repository.find_by_user_and_type(user_id, type_id, authorization_type)
