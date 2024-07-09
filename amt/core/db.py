import logging
from functools import lru_cache

from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
from sqlmodel import Session, SQLModel, create_engine, select, update

from amt.core.config import get_settings
from amt.models import Status, Task, User

logger = logging.getLogger(__name__)


@lru_cache(maxsize=8)
def get_engine() -> Engine:
    settings = get_settings()
    connect_args = (
        {"check_same_thread": False, "isolation_level": None} if settings.APP_DATABASE_SCHEME == "sqlite" else {}
    )
    poolclass = StaticPool if settings.APP_DATABASE_SCHEME == "sqlite" else QueuePool

    return create_engine(
        settings.SQLALCHEMY_DATABASE_URI,  # pyright: ignore [reportArgumentType]
        connect_args=connect_args,
        poolclass=poolclass,
        echo=settings.SQLALCHEMY_ECHO,
    )


def check_db() -> None:
    logger.info("Checking database connection")
    with Session(get_engine()) as session:
        session.exec(select(1))

    logger.info("Finish Checking database connection")


def remove_old_demo_objects(session: Session) -> None:
    task = session.exec(select(Task).where(Task.title == "First task")).first()
    if task:
        session.delete(task)
    session.exec(update(Task).values(status_id=None, user_id=None))  # type: ignore
    user = session.exec(select(User).where(User.name == "Robbert")).first()
    if user:
        session.delete(user)
    status = session.exec(select(Status).where(Status.name == "todo")).first()
    if status:
        session.delete(status)
    session.commit()


def init_db() -> None:
    logger.info("Initializing database")

    if get_settings().AUTO_CREATE_SCHEMA:
        logger.info("Creating database schema")
        SQLModel.metadata.create_all(get_engine())

    with Session(get_engine()) as session:
        if get_settings().ENVIRONMENT == "demo":
            logger.info("Creating demo data")
            remove_old_demo_objects(session)
            add_demo_users(session, ["default user"])
            demo_statuses = add_demo_statuses(session, ["todo", "review", "in_progress", "done"])
            add_demo_tasks(session, demo_statuses[0], 3)
    logger.info("Finished initializing database")


def add_demo_users(session: Session, user_names: list[str]) -> None:
    for user_name in user_names:
        user = session.exec(select(User).where(User.name == user_name)).first()
        if not user:
            session.add(User(name=user_name, avatar=None))
    session.commit()


def add_demo_tasks(session: Session, status: Status | None, number_of_tasks: int) -> None:
    if status is None:
        return
    for index in range(1, number_of_tasks + 1):
        title = "Example task " + str(index)
        task = session.exec(select(Task).where(Task.title == title)).first()
        if not task:
            session.add(
                Task(
                    title=title,
                    description="Example description " + str(index),
                    sort_order=index,
                    status_id=status.id,
                )
            )
    session.exec(update(Task).values(status_id=status.id))  # type: ignore
    session.commit()


def add_demo_statuses(session: Session, statuses: list[str]) -> list[Status]:
    return_statuses: list[Status] = []
    for index, status_name in enumerate(statuses):
        status = session.exec(select(Status).where(Status.name == status_name)).first()
        if not status:
            status = Status(name=status_name, sort_order=index + 1)
            session.add(status)
        return_statuses.append(status)
    session.commit()
    for return_status in return_statuses:
        session.refresh(return_status)
    return return_statuses
