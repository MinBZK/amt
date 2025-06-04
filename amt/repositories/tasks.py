import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy import and_, delete, desc, select, update
from sqlalchemy.exc import NoResultFound

from amt.core.exceptions import AMTRepositoryError
from amt.enums.tasks import Status, TaskType
from amt.models import Task
from amt.repositories.deps import AsyncSessionWithCommitFlag, get_session
from amt.repositories.repository_classes import BaseRepository
from amt.schema.measure import MeasureTask

logger = logging.getLogger(__name__)


class TasksRepository(BaseRepository):
    """
    The TasksRepository provides access to the repository layer.
    """

    def __init__(self, session: Annotated[AsyncSessionWithCommitFlag, Depends(get_session)]) -> None:
        super().__init__(session)

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
        self.session.add(task)
        await self.session.flush()
        self.session.should_commit = True
        return task

    async def save_all(self, tasks: Sequence[Task]) -> None:
        """
        Stores the given tasks in the repository or throws a RepositoryException
        :param tasks: the tasks to store
        :return: the updated tasks after storing
        """
        self.session.add_all(tasks)
        await self.session.flush()
        self.session.should_commit = True

    async def delete(self, task: Task) -> None:
        """
        Deletes the given task in the repository or throws a RepositoryException
        :param task: the task to store
        :return: the updated task after storing
        """
        await self.session.delete(task)
        await self.session.flush()
        self.session.should_commit = True

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

    async def get_last_task(self, algorithm_id: int) -> Task | None:
        statement = select(Task).where(Task.algorithm_id == algorithm_id).order_by(desc(Task.sort_order)).limit(1)
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def add_tasks(
        self, algorithm_id: int, task_type: TaskType, tasks: list[MeasureTask], start_at: float = 0
    ) -> None:
        if tasks:
            insert_list = [
                Task(
                    title="",
                    description="",
                    algorithm_id=algorithm_id,
                    type_id=task.urn,
                    type=task_type,
                    status_id=Status.TODO,
                    sort_order=(start_at + idx * 10),
                )
                for idx, task in enumerate(tasks)
            ]
            await self.save_all(insert_list)
            self.session.should_commit = True

    async def remove_tasks(self, algorithm_id: int, task_type: TaskType, tasks: list[MeasureTask]) -> None:
        task_urns = [task.urn for task in tasks]
        if task_urns:
            statement = (
                delete(Task)
                .where(Task.type_id.in_(task_urns))
                .where(Task.algorithm_id == algorithm_id)
                .where(Task.type == task_type)
            )
            # reminder: session.execute does NOT commit changes
            # this repository uses the get_session which commits for us
            delete_result = await self.session.execute(statement)
            logger.info(f"Removed {delete_result.rowcount} tasks for algorithm_id = {algorithm_id}")
            self.session.should_commit = True

    async def find_by_algorithm_id_and_type(self, algorithm_id: int, task_type: TaskType | None) -> Sequence[Task]:
        statement = select(Task).where(Task.algorithm_id == algorithm_id)
        if task_type:
            statement = statement.where(Task.type == task_type)
        statement = statement.order_by(Task.sort_order)
        try:
            return (await self.session.execute(statement)).scalars().all()
        except NoResultFound:
            logger.exception("No tasks found for algorithm " + str(algorithm_id) + " of type " + str(task_type))
            return []

    async def update_tasks_status(self, algorithm_id: int, task_type: TaskType, type_id: str, status: Status) -> None:
        statement = (
            update(Task)
            .where(Task.algorithm_id == algorithm_id)
            .where(Task.type == task_type)
            .where(Task.type_id == type_id)
            .values(status_id=status)
        )
        await self.session.execute(statement)
        self.session.should_commit = True
