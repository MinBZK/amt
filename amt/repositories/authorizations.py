import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amt.core.authorization import AuthorizationResource, AuthorizationType, AuthorizationVerb
from amt.models import Authorization, Role, Rule, User
from amt.repositories.algorithms import AlgorithmsRepository
from amt.repositories.deps import get_session_non_generator
from amt.repositories.organizations import OrganizationsRepository
from amt.repositories.users import UsersRepository

logger = logging.getLogger(__name__)

PermissionTuple = tuple[AuthorizationResource, list[AuthorizationVerb], AuthorizationType, str | int]
PermissionsList = list[PermissionTuple]


class AuthorizationRepository:
    """
    The AuthorizationRepository provides access to the repository layer.
    """

    def __init__(self, session: AsyncSession | None = None) -> None:
        self.session = session

    async def init_session(self) -> None:
        if self.session is None:
            self.session = await get_session_non_generator()

    async def get_user(self, user_id: UUID) -> User | None:
        try:
            await self.init_session()
            return await UsersRepository(session=self.session).find_by_id(user_id)  # pyright: ignore[reportArgumentType]
        finally:
            if self.session is not None:
                await self.session.close()

    async def find_by_user(self, user: UUID) -> PermissionsList | None:
        """
        Returns all authorization for a user.
        :return: all authorization for the user
        """
        try:
            await self.init_session()
            authorization_verbs: list[AuthorizationVerb] = [
                AuthorizationVerb.READ,
                AuthorizationVerb.UPDATE,
                AuthorizationVerb.CREATE,
                AuthorizationVerb.LIST,
                AuthorizationVerb.DELETE,
            ]
            my_algorithms: PermissionsList = [
                (AuthorizationResource.ALGORITHMS, authorization_verbs, AuthorizationType.ALGORITHM, "*"),
            ]
            my_algorithms += [
                (AuthorizationResource.ALGORITHM, authorization_verbs, AuthorizationType.ALGORITHM, algorithm.id)
                for algorithm in await AlgorithmsRepository(session=self.session).get_by_user(user)  # pyright: ignore[reportArgumentType]
            ]
            my_organizations: PermissionsList = [
                (AuthorizationResource.ORGANIZATIONS, authorization_verbs, AuthorizationType.ORGANIZATION, "*"),
            ]
            my_organizations += [
                (
                    AuthorizationResource.ORGANIZATION_INFO_SLUG,
                    authorization_verbs,
                    AuthorizationType.ORGANIZATION,
                    organization.slug,
                )
                for organization in await OrganizationsRepository(session=self.session).get_by_user(user)  # pyright: ignore[reportArgumentType]
            ]
            return my_algorithms + my_organizations
        finally:
            if self.session is not None:
                await self.session.close()

    async def find_by_user_original(self, user: UUID) -> PermissionsList | None:
        """
        Returns all authorization for a user.
        :return: all authorization for the user
        """
        await self.init_session()

        statement = (
            select(
                Rule.resource,
                Rule.verbs,
                Authorization.type,
                Authorization.type_id,
            )
            .join(Role, Rule.role_id == Role.id)
            .join(Authorization, Rule.role_id == Authorization.role_id)
            .filter(Authorization.user_id == user)
        )

        try:
            result = await self.session.execute(statement)  # type: ignore
            authorizations = result.all()
            # TODO: with close the session to avoid the pool error, but this feels like a work-around, not a fix
            return authorizations  # type: ignore
        finally:
            if self.session is not None:
                await self.session.close()
