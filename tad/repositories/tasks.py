import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from tad.models import Task
from tad.repositories.deps import get_session
from tad.repositories.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class TasksRepository:
    """
    The TasksRepository provides access to the repository layer.
    """

    def __init__(self, session: Annotated[Session, Depends(get_session)]):
        self.session = session

    def find_all(self) -> Sequence[Task]:
        """
        Returns all tasks in the repository.
        :return: all tasks in the repository
        """
        return self.session.exec(select(Task)).all()

    def find_by_status_id(self, status_id: int) -> Sequence[Task]:
        """
        Returns all tasks in the repository for the given status_id.
        :param status_id: the status_id to filter on
        :return: a list of tasks in the repository for the given status_id
        """
        # todo (Robbert): we 'type ignore' Task.sort_order because it works correctly, but pyright does not agree
        statement = select(Task).where(Task.status_id == status_id).order_by(Task.sort_order)  # type: ignore
        return self.session.exec(statement).all()

    def save(self, task: Task) -> Task:
        """
        Stores the given task in the repository or throws a RepositoryException
        :param task: the task to store
        :return: the updated task after storing
        """
        try:
            self.session.add(task)
            self.session.commit()
            self.session.refresh(task)
        except Exception as e:
            self.session.rollback()
            raise RepositoryError from e
        return task

    def find_by_id(self, task_id: int) -> Task:
        """
        Returns the task with the given id.
        :param task_id: the id of the task to find
        :return: the task with the given id or an exception if no task was found
        """
        statement = select(Task).where(Task.id == task_id)
        try:
            return self.session.exec(statement).one()
        except NoResultFound as e:
            raise RepositoryError from e
