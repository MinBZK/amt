import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from amt.core.config import get_settings
from amt.models.base import Base

logger = logging.getLogger(__name__)


def get_engine() -> AsyncEngine:
    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.APP_DATABASE_SCHEME == "sqlite" else {}

    return create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,  # pyright: ignore [reportArgumentType]
        connect_args=connect_args,
        echo=settings.SQLALCHEMY_ECHO,
    )


async def check_db() -> None:
    logger.info("Checking database connection")
    async with AsyncSession(get_engine()) as session:
        await session.execute(select(1))

    logger.info("Finish Checking database connection")


async def init_db() -> None:
    logger.info("Initializing database")

    if get_settings().AUTO_CREATE_SCHEMA:  # pragma: no cover
        logger.info("Creating database schema")
        engine = get_engine()
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    logger.info("Finished initializing database")
