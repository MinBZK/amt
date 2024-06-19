import logging
from functools import lru_cache

from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from tad.core.config import get_settings
from tad.models import Status, Task, User

logger = logging.getLogger(__name__)


@lru_cache(maxsize=8)
def get_engine() -> Engine:
    connect_args = (
        {"check_same_thread": False, "isolation_level": None} if get_settings().APP_DATABASE_SCHEME == "sqlite" else {}
    )
    poolclass = StaticPool if get_settings().APP_DATABASE_SCHEME == "sqlite" else QueuePool

    return create_engine(
        str(get_settings().SQLALCHEMY_DATABASE_URI),
        connect_args=connect_args,
        poolclass=poolclass,
        echo=get_settings().SQLALCHEMY_ECHO,
    )


def check_db():
    logger.info("Checking database connection")
    with Session(get_engine()) as session:
        session.exec(select(1))

    logger.info("Finisch Checking database connection")


def init_db():
    logger.info("Initializing database")

    if get_settings().AUTO_CREATE_SCHEMA:
        logger.info("Creating database schema")
        SQLModel.metadata.create_all(get_engine())

    with Session(get_engine()) as session:
        if get_settings().ENVIRONMENT == "demo":
            logger.info("Creating demo data")

            user = session.exec(select(User).where(User.name == "Robbert")).first()
            if not user:
                user = User(name="Robbert", avatar=None)
                session.add(user)

            status = session.exec(select(Status).where(Status.name == "Todo")).first()
            if not status:
                status = Status(name="Todo", sort_order=1)
                session.add(status)

            task = session.exec(select(Task).where(Task.title == "First task")).first()
            if not task:
                task = Task(title="First task", description="This is the first task", sort_order=1, status_id=status.id)
                session.add(task)
            session.commit()
    logger.info("Finished initializing database")
