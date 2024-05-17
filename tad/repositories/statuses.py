import logging
from collections.abc import Sequence

from sqlmodel import Session, select

from tad.core.db import engine
from tad.models import Status

logger = logging.getLogger(__name__)


class StatusesRepository:
    # TODO find out how to reuse Session

    @staticmethod
    def create_example_statuses():
        statuses = StatusesRepository.find_all()
        if len(statuses) == 0:
            with Session(engine) as session:
                session.add(Status(id=1, name="todo", sort_order=1))
                session.add(Status(id=2, name="in_progress", sort_order=2))
                session.add(Status(id=3, name="review", sort_order=3))
                session.add(Status(id=4, name="done", sort_order=4))
                session.commit()

    @staticmethod
    def find_all() -> Sequence[Status]:
        with Session(engine) as session:
            statement = select(Status)
            return session.exec(statement).all()

    @staticmethod
    def save(status) -> Status:
        with Session(engine) as session:
            session.add(status)
            session.commit()
            session.refresh(status)
            return status

    @staticmethod
    def find_by_id(status_id) -> Status:
        """
        Returns the status with the given id or an exception if the id does not exist.
        :param status_id: the id of the status
        :return: the status with the given id or an exception
        """
        with Session(engine) as session:
            statement = select(Status).where(Status.id == status_id)
            return session.exec(statement).one()
