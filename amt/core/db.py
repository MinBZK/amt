import logging

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine, select, update

from amt.core.config import get_settings
from amt.enums.status import Status
from amt.models import Task, User

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


def remove_old_demo_objects(session: Session) -> None:
    task = session.exec(select(Task).where(Task.title == "First task")).first()
    if task:
        session.delete(task)
    session.exec(update(Task).values(status_id=None, user_id=None))  # type: ignore
    user = session.exec(select(User).where(User.name == "Robbert")).first()
    if user:
        session.delete(user)
    session.commit()


def init_db() -> None:
    logger.info("Initializing database")

    if get_settings().AUTO_CREATE_SCHEMA:  # pragma: no cover
        logger.info("Creating database schema")
        SQLModel.metadata.create_all(get_engine())

    with Session(get_engine()) as session:  # pragma: no cover
        if get_settings().ENVIRONMENT == "demo":
            logger.info("Creating demo data")
            remove_old_demo_objects(session)
            add_demo_users(session, ["default user"])
            add_demo_tasks(session, Status.TODO, 3)
    logger.info("Finished initializing database")


def add_demo_users(session: Session, user_names: list[str]) -> None:
    for user_name in user_names:
        user = session.exec(select(User).where(User.name == user_name)).first()
        if not user:
            session.add(User(name=user_name, avatar=None))
    session.commit()


def add_demo_tasks(session: Session, status: Status, number_of_tasks: int) -> None:
    for index in range(1, number_of_tasks + 1):
        title = "Example task " + str(index)
        task = session.exec(select(Task).where(Task.title == title)).first()
        if not task:
            session.add(
                Task(title=title, description="Example description " + str(index), sort_order=index, status_id=status)
            )
    session.exec(update(Task).values(status_id=status))  # type: ignore
    session.commit()
