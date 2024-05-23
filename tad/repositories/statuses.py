import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, select

from tad.models import Status
from tad.repositories.deps import get_session

logger = logging.getLogger(__name__)


class StatusesRepository:
    def __init__(self, session: Annotated[Session, Depends(get_session)]):
        self.session = session

    def create_example_statuses(self):
        if len(self.find_all()) == 0:
            self.session.add(Status(id=1, name="todo", sort_order=1))
            self.session.add(Status(id=2, name="in_progress", sort_order=2))
            self.session.add(Status(id=3, name="review", sort_order=3))
            self.session.add(Status(id=4, name="done", sort_order=4))
            self.session.commit()

    def find_all(self) -> Sequence[Status]:
        statement = select(Status)
        return self.session.exec(statement).all()

    def save(self, status) -> Status:
        self.session.add(status)
        self.session.commit()
        self.session.refresh(status)
        return status

    def find_by_id(self, status_id) -> Status:
        """
        Returns the status with the given id or an exception if the id does not exist.
        :param status_id: the id of the status
        :return: the status with the given id or an exception
        """
        statement = select(Status).where(Status.id == status_id)
        return self.session.exec(statement).one()
