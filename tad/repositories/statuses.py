import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from tad.core.exceptions import RepositoryError
from tad.models import Status
from tad.repositories.deps import get_session

logger = logging.getLogger(__name__)


class StatusesRepository:
    """
    The StatusRepository provides access to the repository layer.
    """

    def __init__(self, session: Annotated[Session, Depends(get_session)]) -> None:
        self.session = session

    def find_all(self) -> Sequence[Status]:
        """
        Returns a list of all statuses in the repository ordered by sort order.
        :return: the list of all statuses
        """
        return self.session.exec(select(Status).order_by(Status.sort_order)).all()  # pyright: ignore [reportUnknownMemberType, reportCallIssue, reportUnknownVariableType, reportArgumentType]

    def save(self, status: Status) -> Status:
        """
        Stores the given status in the repository.
        :param status: the status to store
        :return: the updated status after storing
        """
        try:
            self.session.add(status)
            self.session.commit()
            self.session.refresh(status)
        except Exception as e:
            self.session.rollback()
            raise RepositoryError from e
        return status

    def delete(self, status: Status) -> None:
        """
        Deletes the given status in the repository.
        :param status: the status to store
        :return: the updated status after storing
        """
        try:
            self.session.delete(status)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise RepositoryError from e
        return None

    def find_by_id(self, status_id: int) -> Status:
        """
        Returns the status with the given id or an exception if the id does not exist.
        :param status_id: the id of the status
        :return: the status with the given id or an exception
        """
        try:
            statement = select(Status).where(Status.id == status_id)
            return self.session.exec(statement).one()
        except NoResultFound as e:
            raise RepositoryError from e
