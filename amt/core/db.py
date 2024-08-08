import logging

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine, select

from amt.core.config import get_settings

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.APP_DATABASE_SCHEME == "sqlite" else {}

    return create_engine(
        settings.SQLALCHEMY_DATABASE_URI,  # pyright: ignore [reportArgumentType]
        connect_args=connect_args,
        echo=settings.SQLALCHEMY_ECHO,
    )


def check_db() -> None:
    logger.info("Checking database connection")
    with Session(get_engine()) as session:
        session.exec(select(1))

    logger.info("Finish Checking database connection")


def init_db() -> None:
    logger.info("Initializing database")

    if get_settings().AUTO_CREATE_SCHEMA:  # pragma: no cover
        logger.info("Creating database schema")
        SQLModel.metadata.create_all(get_engine())

    logger.info("Finished initializing database")
