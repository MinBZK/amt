from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from amt.core.db import get_engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session_factory = async_sessionmaker(
        get_engine(),
        expire_on_commit=False,
        class_=AsyncSession,
    )
    async with async_session_factory() as async_session:
        yield async_session


async def get_session_non_generator() -> AsyncSession:
    async_session_factory = async_sessionmaker(
        get_engine(),
        expire_on_commit=False,
        class_=AsyncSession,
    )
    return async_session_factory()
