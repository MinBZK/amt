import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends

from amt.enums.tasks import Status, TaskType
from amt.models.algorithm import Algorithm
from amt.models.task import Task
from amt.models.user import User
from amt.repositories.tasks import TasksRepository
from amt.schema.instrument import InstrumentTask
from amt.schema.system_card import SystemCard
from amt.services.storage import StorageFactory

logger = logging.getLogger(__name__)


class TasksService:
    def __init__(
        self,
        repository: Annotated[TasksRepository, Depends(TasksRepository)],
    ) -> None:
        self.repository = repository
        self.storage_writer = StorageFactory.init(storage_type="file", location="./output", filename="system_card.yaml")
        self.system_card = SystemCard(version="0.0.0")  # pyright: ignore[reportCallIssue]

    async def get_tasks(self, status_id: int) -> Sequence[Task]:
        task = await self.repository.find_by_status_id(status_id)
        return task

    async def get_tasks_for_algorithm(self, algorithm_id: int, task_type: TaskType | None) -> Sequence[Task]:
        return await self.repository.find_by_algorithm_id_and_type(algorithm_id, task_type)

    async def assign_task(self, task: Task, user: User) -> Task:
        task.user_id = user.id
        return await self.repository.save(task)

    async def create_instrument_tasks(self, tasks: Sequence[InstrumentTask], algorithm: Algorithm) -> None:
        # TODO: (Christopher) At this moment a status has to be retrieved from the DB. In the future
        #       we will have static statuses, so this will need to change.
        status = Status.TODO
        await self.repository.save_all(
            [
                # TODO: (Christopher) The ticket does not specify what to do when question type is not an
                # open questions, hence for now all titles will be set to task.question.
                Task(
                    title=task.question[:1024],
                    description="",
                    algorithm_id=algorithm.id,
                    status_id=status,
                    sort_order=idx,
                )
                for idx, task in enumerate(tasks)
            ]
        )

    async def move_task(
        self,
        task_id: int | None,
        status_id: int | None,
        previous_sibling_id: int | None = None,
        next_sibling_id: int | None = None,
    ) -> Task:
        """
        Updates the task with the given task_id
        :param task_id: the id of the task
        :param status_id: the id of the status of the task
        :param previous_sibling_id: the id of the previous sibling of the task or None
        :param next_sibling_id: the id of the next sibling of the task or None
        :return: the updated task
        """
        if task_id is None or status_id is None:
            raise ValueError("task_id or status_id must not be None")
        task = await self.repository.find_by_id(task_id)

        # update the status for the task (this may not be needed if the status has not changed)
        task.status_id = status_id

        # update order position of the card
        if previous_sibling_id and next_sibling_id:
            previous_task = await self.repository.find_by_id(previous_sibling_id)
            next_task = await self.repository.find_by_id(next_sibling_id)
            new_sort_order = previous_task.sort_order + ((next_task.sort_order - previous_task.sort_order) / 2)
            task.sort_order = new_sort_order
        elif previous_sibling_id and not next_sibling_id:
            previous_task = await self.repository.find_by_id(previous_sibling_id)
            task.sort_order = previous_task.sort_order + 10
        elif not previous_sibling_id and next_sibling_id:
            next_task = await self.repository.find_by_id(next_sibling_id)
            task.sort_order = next_task.sort_order / 2
        else:
            task.sort_order = 10

        return await self.repository.save(task)

    async def update_tasks_status(self, algorithm_id: int, task_type: TaskType, type_id: str, status: Status) -> None:
        await self.repository.update_tasks_status(algorithm_id, task_type, type_id, status)

    async def find_by_algorithm_id_and_status_id(self, algorithm_id: int, status_id: int) -> Sequence[Task]:
        return await self.repository.find_by_algorithm_id_and_status_id(algorithm_id, status_id)
