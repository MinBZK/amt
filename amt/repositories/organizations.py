import logging
from collections.abc import Sequence
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy import Select, func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import lazyload
from sqlalchemy_utils import escape_like  # pyright: ignore[reportMissingTypeStubs, reportUnknownVariableType]

from amt.api.organization_filter_options import OrganizationFilterOptions
from amt.core.authorization import AuthorizationType
from amt.core.exceptions import AMTRepositoryError
from amt.models import Authorization, Organization
from amt.repositories.deps import AsyncSessionWithCommitFlag, get_session
from amt.repositories.repository_classes import BaseRepository

logger = logging.getLogger(__name__)


class OrganizationsRepository(BaseRepository):
    def __init__(self, session: Annotated[AsyncSessionWithCommitFlag, Depends(get_session)]) -> None:
        super().__init__(session)

    def _as_count_query(self, statement: Select[Any]) -> Select[Any]:
        statement = statement.with_only_columns(func.count()).order_by(None)
        statement = statement.options(lazyload("*"))
        return statement

    def _find_by(  # noqa
        self,
        sort: dict[str, str] | None = None,
        filters: dict[str, str] | None = None,
        user_id: str | UUID | None = None,
        search: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Select[Any]:
        user_id = UUID(user_id) if isinstance(user_id, str) else user_id
        statement = select(Organization)
        if search:
            statement = statement.filter(Organization.name.ilike(f"%{escape_like(search)}%"))
        if (
            filters
            and user_id
            and "organization-type" in filters
            and filters["organization-type"] == OrganizationFilterOptions.MY_ORGANIZATIONS.value
        ):
            statement = (
                statement.where(Authorization.type_id == Organization.id)
                .where(Authorization.user_id == user_id)
                .where(Authorization.type == AuthorizationType.ORGANIZATION)
            )

        if sort:
            if "name" in sort and sort["name"] == "ascending":
                statement = statement.order_by(func.lower(Organization.name).asc())
            elif "name" in sort and sort["name"] == "descending":
                statement = statement.order_by(func.lower(Organization.name).desc())
            elif "last_update" in sort and sort["last_update"] == "ascending":
                statement = statement.order_by(Organization.modified_at.asc())
            elif "last_update" in sort and sort["last_update"] == "descending":
                statement = statement.order_by(Organization.modified_at.desc())
        statement = statement.where(Organization.deleted_at.is_(None))
        if skip:
            statement = statement.offset(skip)
        if limit:
            statement = statement.limit(limit)
        # to force lazy-loading, use line below
        # statement = statement.options(lazyload('*')) # noqa
        return statement

    async def find_by(
        self,
        sort: dict[str, str] | None = None,
        filters: dict[str, str] | None = None,
        user_id: str | UUID | None = None,
        search: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Sequence[Organization]:
        statement = self._find_by(sort=sort, filters=filters, user_id=user_id, search=search, skip=skip, limit=limit)
        return (await self.session.execute(statement)).scalars().all()

    async def find_by_as_count(
        self,
        sort: dict[str, str] | None = None,
        filters: dict[str, str] | None = None,
        user_id: str | UUID | None = None,
        search: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Any:  # noqa
        statement = self._find_by(sort=sort, filters=filters, user_id=user_id, search=search, skip=skip, limit=limit)
        statement = self._as_count_query(statement)
        return (await self.session.execute(statement)).scalars().first()

    async def save(self, organization: Organization) -> Organization:
        self.session.add(organization)
        await self.session.flush()
        self.session.should_commit = True
        return organization

    async def find_by_slug(self, slug: str) -> Organization:
        try:
            statement = select(Organization).where(Organization.slug == slug).where(Organization.deleted_at.is_(None))
            return (await self.session.execute(statement)).scalars().one()
        except NoResultFound as e:
            logger.exception("Organization not found")
            raise AMTRepositoryError from e

    async def find_by_id(self, organization_id: int) -> Organization:
        try:
            statement = (
                select(Organization).where(Organization.id == organization_id).where(Organization.deleted_at.is_(None))
            )
            return (await self.session.execute(statement)).scalars().one()
        except NoResultFound as e:
            logger.exception("Organization not found")
            raise AMTRepositoryError from e

    async def find_by_id_and_user_id(self, organization_id: int, user_id: str | UUID) -> Organization:
        user_id = UUID(user_id) if isinstance(user_id, str) else user_id
        # usage: to make sure a user is actually part of an organization
        try:
            statement = (
                select(Organization)
                .join(Authorization, Authorization.type_id == Organization.id)
                .where(Authorization.user_id == user_id)
                .where(Authorization.type == AuthorizationType.ORGANIZATION)
                .where(Organization.id == organization_id)
                .where(Organization.deleted_at.is_(None))
            )
            return (await self.session.execute(statement)).scalars().one()
        except NoResultFound as e:
            logger.exception("Organization not found")
            raise AMTRepositoryError from e

    async def get_by_user(self, user_id: UUID) -> Sequence[Organization]:
        statement = (
            select(Organization)
            .join(Authorization, Authorization.type_id == Organization.id)
            .where(Authorization.user_id == user_id)
            .where(Authorization.type == AuthorizationType.ORGANIZATION)
            .where(Organization.deleted_at.is_(None))
        )
        return (await self.session.execute(statement)).scalars().all()
