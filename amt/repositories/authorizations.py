import logging
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from amt.models import Authorization, Role
from amt.repositories.deps import get_session

logger = logging.getLogger(__name__)


class AuthorizationRepository:
    """
    The TasksRepository provides access to the repository layer.
    """

    def __init__(self) -> None:
        self.session = get_session()

    async def find_by_user(self, user: UUID) -> Sequence[Authorization]:
        """
        Returns all authorization for a user.
        :return: all authorization for the user
        """
        statement = (
            select(Authorization, Role).where(Authorization.user_id == user).filter(Role.id == Authorization.role_id)
        )
        session = await self.session.__anext__()

        return (await session.execute(statement)).scalars().all()
