import logging
from collections.abc import Sequence

from sqlmodel import Session, select

from tad.core.db import engine
from tad.core.singleton import Singleton
from tad.models import Status

logger = logging.getLogger(__name__)


class StatusesRepository(metaclass=Singleton):
    # TODO find out how to reuse Session

    def __init__(self):
        logger.info("Hello world from statuses repo")
        statuses = self.find_all()
        if len(statuses) == 0:
            self.__add_test_statuses()

    def __add_test_statuses(self):
        with Session(engine) as session:
            session.add(Status(id=1, name="todo", sort_order=1))
            session.add(Status(id=2, name="in_progress", sort_order=2))
            session.add(Status(id=3, name="review", sort_order=3))
            session.add(Status(id=4, name="done", sort_order=4))
            session.commit()

    def find_all(self) -> Sequence[Status]:
        with Session(engine) as session:
            statement = select(Status)
            return session.exec(statement).all()

    def save(self, status) -> Status:
        with Session(engine) as session:
            session.add(status)
            session.commit()
            session.refresh(status)
            return status

    def find_by_id(self, status_id) -> Status:
        with Session(engine) as session:
            statement = select(Status).where(Status.id == status_id)
            return session.exec(statement).one()
