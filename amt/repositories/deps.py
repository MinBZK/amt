import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from amt.core.db import get_engine
from amt.core.exceptions import AMTRepositoryError

logger = logging.getLogger(__name__)


class AsyncSessionWithCommitFlag(AsyncSession):
    """
    Extended AsyncSession to include a flag to indicate if the session should be committed.

    We use this approach because we use a transaction manager that will commit at the end of a transaction.
    However, changes can be made which should not be persisted, therefor
    using the default checks, like session.dirty will not work.

    Methods that make changes and want to persist those must set the should_commit to True.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa ANN401
        super().__init__(*args, **kwargs)
        self._should_commit: bool = False

    @property
    def should_commit(self) -> bool:
        """Returns whether this session should be committed"""
        return self._should_commit

    @should_commit.setter
    def should_commit(self, value: bool) -> None:
        """Sets whether this session should be committed"""
        self._should_commit = value


async def get_session() -> AsyncGenerator[AsyncSessionWithCommitFlag, None]:
    """Provides either a read-only or auto-commit session based on the mode"""
    async_session_factory = async_sessionmaker(
        get_engine(),
        expire_on_commit=False,
        class_=AsyncSessionWithCommitFlag,
    )

    async with async_session_factory() as session, transaction_context(session) as tx_session:
        tx_session.info["id"] = str(id(tx_session)) + " (auto-commit)"
        yield tx_session


async def get_session_non_generator() -> AsyncSessionWithCommitFlag:
    async_session_factory = async_sessionmaker(
        get_engine(),
        expire_on_commit=False,
        class_=AsyncSessionWithCommitFlag,
    )
    async_session = async_session_factory()
    async_session.info["id"] = id(async_session)
    return async_session


@asynccontextmanager
async def transaction_context(session: AsyncSessionWithCommitFlag) -> AsyncGenerator[AsyncSessionWithCommitFlag, None]:
    try:
        yield session
        if session.should_commit:
            await session.commit()
        else:
            logger.warning("No commit flag found, not committing transaction")
    except Exception as e:
        if session.should_commit:
            await session.rollback()
        if isinstance(e, DatabaseError):
            raise AMTRepositoryError from e
        else:
            raise
