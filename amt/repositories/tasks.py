import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy import and_, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from amt.core.exceptions import AMTRepositoryError
from amt.models import Task
from amt.repositories.deps import get_session

logger = logging.getLogger(__name__)


class TasksRepository:
    """
    The TasksRepository provides access to the repository layer.
    """

    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]) -> None:
        self.session = session

    async def find_all(self) -> Sequence[Task]:
        """
        Returns all tasks in the repository.
        :return: all tasks in the repository
        """
        return (await self.session.execute(select(Task))).scalars().all()

    async def find_by_status_id(self, status_id: int) -> Sequence[Task]:
        """
        Returns all tasks in the repository for the given status_id.
        :param status_id: the status_id to filter on
        :return: a list of tasks in the repository for the given status_id
        """
        statement = select(Task).where(Task.status_id == status_id).order_by(Task.sort_order)
        return (await self.session.execute(statement)).scalars().all()

    async def find_by_algorithm_id_and_status_id(self, algorithm_id: int, status_id: int) -> Sequence[Task]:
        """
        Returns all tasks in the repository for the given algorithm_id.
        :param algorithm_id: the algorithm_id to filter on
        :return: a list of tasks in the repository for the given algorithm_id
        """
        statement = (
            select(Task)
            .where(and_(Task.status_id == status_id, Task.algorithm_id == algorithm_id))
            .order_by(Task.sort_order)
        )
        return (await self.session.execute(statement)).scalars().all()

    async def save(self, task: Task) -> Task:
        """
        Stores the given task in the repository or throws a RepositoryException
        :param task: the task to store
        :return: the updated task after storing
        """
        try:
            self.session.add(task)
            await self.session.commit()
            await self.session.refresh(task)
        except Exception as e:
            logger.exception("Could not store task")
            await self.session.rollback()
            raise AMTRepositoryError from e
        return task

    async def save_all(self, tasks: Sequence[Task]) -> None:
        """
        Stores the given tasks in the repository or throws a RepositoryException
        :param tasks: the tasks to store
        :return: the updated tasks after storing
        """
        try:
            self.session.add_all(tasks)
            await self.session.commit()
        except Exception as e:
            logger.exception("Could not store all tasks")
            await self.session.rollback()
            raise AMTRepositoryError from e

    async def delete(self, task: Task) -> None:
        """
        Deletes the given task in the repository or throws a RepositoryException
        :param task: the task to store
        :return: the updated task after storing
        """
        try:
            await self.session.delete(task)
            await self.session.commit()
        except Exception as e:
            logger.exception("Could not delete task")
            await self.session.rollback()
            raise AMTRepositoryError from e
        return None

    async def find_by_id(self, task_id: int) -> Task:
        """
        Returns the task with the given id.
        :param task_id: the id of the task to find
        :return: the task with the given id or an exception if no task was found
        """
        statement = select(Task).where(Task.id == task_id)
        try:
            return (await self.session.execute(statement)).scalars().one()
        except NoResultFound as e:
            logger.exception("Task not found")
            raise AMTRepositoryError from e
