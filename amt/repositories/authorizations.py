import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amt.core.authorization import AuthorizationVerb
from amt.models import Authorization, Role, Rule
from amt.repositories.deps import get_session_non_generator

logger = logging.getLogger(__name__)

PermissionTuple = tuple[str, list[AuthorizationVerb], str, int]
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

    async def find_by_user(self, user: UUID) -> PermissionsList | None:
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
