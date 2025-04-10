import logging
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends
from sqlalchemy import delete, func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy_utils import escape_like  # pyright: ignore[reportMissingTypeStubs, reportUnknownVariableType]

from amt.core.authorization import AuthorizationResource, AuthorizationType, AuthorizationVerb
from amt.core.exceptions import AMTRepositoryError
from amt.models import Algorithm, Authorization, Organization, Role, Rule, User
from amt.repositories.algorithms import AlgorithmsRepository
from amt.repositories.deps import AsyncSessionWithCommitFlag, get_session
from amt.repositories.organizations import OrganizationsRepository
from amt.repositories.repository_classes import BaseRepository
from amt.repositories.users import UsersRepository

logger = logging.getLogger(__name__)

PermissionTuple = tuple[AuthorizationResource, list[AuthorizationVerb], AuthorizationType, str | int]
PermissionsList = list[PermissionTuple]


class AuthorizationRepository(BaseRepository):
    """
    The AuthorizationRepository provides access to the repository layer.
    """

    def __init__(
        self,
        users_repository: UsersRepository,
        organizations_repository: OrganizationsRepository,
        algorithms_repository: AlgorithmsRepository,
        session: Annotated[AsyncSessionWithCommitFlag, Depends(get_session)],
    ) -> None:
        super().__init__(session)
        self.users_repository = users_repository
        self.organizations_repository = organizations_repository
        self.algorithms_repository = algorithms_repository

    async def get_user(self, user_id: UUID) -> User | None:
        return await self.users_repository.find_by_id(user_id)  # pyright: ignore[reportArgumentType]

    async def get_role_for_user(
        self, user_id: UUID, role_type: AuthorizationType, type_id: int
    ) -> Authorization | None:
        statement = (
            select(Authorization)
            .where(Authorization.user_id == user_id)
            .where(Authorization.type == role_type)
            .where(Authorization.type_id == type_id)
        )
        try:
            return (await self.session.execute(statement)).scalars().one()
        except NoResultFound:
            return None

    async def add_role_for_user(
        self, user_id: UUID | str, role_id: int, role_type: AuthorizationType, type_id: int
    ) -> None:
        user_id = UUID(user_id) if isinstance(user_id, str) else user_id
        authorization = await self.get_role_for_user(user_id, role_type, type_id)
        if authorization:
            authorization.role_id = role_id
        else:
            authorization = Authorization(
                user_id=user_id,
                role_id=role_id,
                type=role_type,
                type_id=type_id,
            )
        self.session.add(authorization)
        self.session.should_commit = True

    @staticmethod
    def get_default_permissions() -> PermissionsList:
        return [
            (
                AuthorizationResource.ORGANIZATIONS,
                [AuthorizationVerb.LIST, AuthorizationVerb.CREATE],
                AuthorizationType.ORGANIZATION,
                "*",
            ),
            (
                # we require 'create' permissions because the algorithms path is not bound to any organization
                AuthorizationResource.ALGORITHMS,
                [AuthorizationVerb.LIST, AuthorizationVerb.CREATE],
                AuthorizationType.ALGORITHM,
                "*",
            ),
        ]

    async def find_by_user(self, user_id: UUID) -> PermissionsList:
        """
        Returns all authorization for a user.
        :return: all authorization for the user
        """
        statement = (
            select(
                Rule.resource,
                Rule.verbs,
                Authorization.type,
                Authorization.type_id,
            )
            .join(Role, Rule.role_id == Role.id)
            .join(Authorization, Rule.role_id == Authorization.role_id)
            .filter(Authorization.user_id == user_id)
        )
        return cast(PermissionsList, (await self.session.execute(statement)).fetchall())

    async def _remove_roles(self, user_id: str | UUID, role_type: AuthorizationType, type_ids: list[int] | int) -> None:
        user_id = UUID(user_id) if isinstance(user_id, str) else user_id
        if not isinstance(type_ids, list):
            type_ids = [type_ids]
        statement = (
            delete(Authorization)
            .where(Authorization.type_id.in_(type_ids))
            .where(Authorization.type == role_type)
            .where(Authorization.user_id == user_id)
        )
        self.session.should_commit = True
        await self.session.execute(statement)

    async def remove_algorithm_roles(self, user_id: str | UUID, algorithm: Algorithm | list[Algorithm]) -> None:
        ids = [algorithm.id for algorithm in algorithm] if isinstance(algorithm, list) else [algorithm.id]
        return await self._remove_roles(user_id, AuthorizationType.ALGORITHM, ids)

    async def remove_all_roles(self, user_id: str | UUID, organization: Organization) -> None:
        """
        Removes all roles for a user, related to the organization and the
        algorithms from this organization.
        """
        user_id = UUID(user_id) if isinstance(user_id, str) else user_id
        algorithms = await self.algorithms_repository.get_by_user(user_id)
        await self.remove_algorithm_roles(user_id, list(algorithms))
        await self._remove_roles(user_id, AuthorizationType.ORGANIZATION, organization.id)
        self.session.should_commit = True
        await self.session.flush()

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
        statement = (
            select(User, Authorization, Role)
            .join(Authorization, Authorization.user_id == User.id)
            .join(Role, Authorization.role_id == Role.id)
            .where(Authorization.type_id == type_id)
            .where(Authorization.type == authorization_type)
        )
        if search:
            statement = statement.filter(User.name.ilike(f"%{escape_like(search)}%"))
        if sort:
            if "name" in sort and sort["name"] == "ascending":
                statement = statement.order_by(func.lower(User.name).asc())
            elif "name" in sort and sort["name"] == "descending":
                statement = statement.order_by(func.lower(User.name).desc())
        if skip:
            statement = statement.offset(skip)
        if limit:
            statement = statement.limit(limit)
        return cast(list[tuple[User, Authorization, Role]], (await self.session.execute(statement)).fetchall())

    async def get_by_id(self, authorization_id: int) -> Authorization | None:
        statement = select(Authorization).where(Authorization.id == authorization_id)
        try:
            return (await self.session.execute(statement)).scalars().one()
        except NoResultFound:
            return None

    async def get_role_by_id(self, role_id: int) -> Role | None:
        statement = select(Role).where(Role.id == role_id)
        try:
            return (await self.session.execute(statement)).scalars().one()
        except NoResultFound:
            return None

    async def get_role(self, role_name: str) -> Role:
        statement = select(Role).where(Role.name == role_name)
        try:
            return (await self.session.execute(statement)).scalars().one()
        except NoResultFound as e:
            raise AMTRepositoryError("Role not found") from e

    async def save(self, authorization: Authorization) -> Authorization:
        self.session.add(authorization)
        await self.session.flush()
        self.session.should_commit = True
        return authorization

    async def find_all(  # noqa C901
        self,
        search: str | None = None,
        sort: dict[str, str] | None = None,
        filters: dict[str, str | int | list[str | int]] | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> list[tuple[User, Authorization, Role]]:
        statement = (
            select(User, Authorization, Role)
            .join(Authorization, Authorization.user_id == User.id)
            .join(Role, Authorization.role_id == Role.id)
        )

        if search:
            statement = statement.filter(User.name.ilike(f"%{escape_like(search)}%"))
        if filters and "user_id" in filters:
            statement = statement.filter(User.id == filters["user_id"])
        if filters and "type" in filters:
            statement = statement.where(
                Authorization.type == filters["type"],
            )
        if filters and "type_id" in filters:
            statement = statement.where(
                Authorization.type_id == filters["type_id"],
            )
        if sort:
            if "name" in sort and sort["name"] == "ascending":
                statement = statement.order_by(func.lower(User.name).asc())
            elif "name" in sort and sort["name"] == "descending":
                statement = statement.order_by(func.lower(User.name).desc())
        if skip:
            statement = statement.offset(skip)
        if limit:
            statement = statement.limit(limit)
        return cast(list[tuple[User, Authorization, Role]], (await self.session.execute(statement)).fetchall())

    async def find_by_user_and_type(
        self, user_id: str | UUID, type_id: int, authorization_type: AuthorizationType
    ) -> Authorization:
        user_id = UUID(user_id) if isinstance(user_id, str) else user_id
        statement = (
            select(Authorization)
            .where(Authorization.user_id == user_id)
            .where(Authorization.type == authorization_type)
            .where(Authorization.type_id == type_id)
        )
        try:
            return (await self.session.execute(statement)).scalars().one()
        except NoResultFound as e:
            raise AMTRepositoryError("Authorization not found") from e
