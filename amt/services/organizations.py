import logging
from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from amt.api.organization_filter_options import OrganizationFilterOptions
from amt.core.exceptions import AMTAuthorizationError
from amt.models import Organization
from amt.models.user import User
from amt.repositories.organizations import OrganizationsRepository
from amt.services.users import UsersService

logger = logging.getLogger(__name__)


class OrganizationsService:
    def __init__(
        self,
        organizations_repository: Annotated[OrganizationsRepository, Depends(OrganizationsRepository)],
        users_service: Annotated[UsersService, Depends(UsersService)],
    ) -> None:
        self.organizations_repository: OrganizationsRepository = organizations_repository
        self.users_service: UsersService = users_service

    async def save(self, name: str, slug: str, user_ids: list[str], created_by_user_id: str | None) -> Organization:
        organization = Organization()
        organization.name = name
        organization.slug = slug
        users: list[User | None] = [await self.users_service.find_by_id(user_id) for user_id in user_ids]
        organization.users = users
        created_by_user = (await self.users_service.find_by_id(created_by_user_id)) if created_by_user_id else None
        organization.created_by = created_by_user
        return await self.organizations_repository.save(organization)

    async def get_organizations_for_user(self, user_id: str | UUID | None) -> Sequence[Organization]:
        # TODO (Robbert): this is not the right place to throw permission denied,
        #  a different error should be raised here
        if not user_id:
            raise AMTAuthorizationError()

        user_id = UUID(user_id) if isinstance(user_id, str) else user_id

        return await self.organizations_repository.find_by(
            sort={"name": "ascending"},
            filters={"organization-type": OrganizationFilterOptions.MY_ORGANIZATIONS.value},
            user_id=user_id,
        )

    async def add_users(self, organization: Organization, user_ids: list[str] | str) -> Organization:
        new_users: list[User | None] = [await self.users_service.find_by_id(user_id) for user_id in user_ids]
        for user in new_users:
            if user not in organization.users:  # pyright: ignore[reportUnknownMemberType]
                organization.users.append(user)  # pyright: ignore[reportUnknownMemberType]
        return await self.organizations_repository.save(organization)

    async def find_by_slug(self, slug: str) -> Organization:
        return await self.organizations_repository.find_by_slug(slug)

    async def get_by_id(self, organization_id: int) -> Organization:
        return await self.organizations_repository.find_by_id(organization_id)

    async def find_by_id_and_user_id(self, organization_id: int, user_id: str | UUID) -> Organization:
        return await self.organizations_repository.find_by_id_and_user_id(organization_id, user_id)

    async def update(self, organization: Organization) -> Organization:
        return await self.organizations_repository.save(organization)

    async def remove_user(self, organization: Organization, user: User) -> Organization:
        return await self.organizations_repository.remove_user(organization, user)
