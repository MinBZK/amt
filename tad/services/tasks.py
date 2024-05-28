import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends

from tad.models.task import Task
from tad.models.user import User
from tad.repositories.tasks import TasksRepository
from tad.services.statuses import StatusesService
from tad.services.storage import FileSystemWriteService
from tad.services.system_card import SystemCardService

logger = logging.getLogger(__name__)


class TasksService:
    def __init__(
        self,
        statuses_service: Annotated[StatusesService, Depends(StatusesService)],
        repository: Annotated[TasksRepository, Depends(TasksRepository)],
        system_card_service: Annotated[SystemCardService, Depends(SystemCardService)],
        storage_service: Annotated[FileSystemWriteService, Depends(FileSystemWriteService)],
    ):
        self.repository = repository
        self.statuses_service = statuses_service
        self.system_card_service = system_card_service
        location = "./tests/data"
        filename = "system_card.yaml"
        self.storage_service = storage_service.__init__(location, filename)  # TODO is this okay @robbert?

    def get_tasks(self, status_id: int) -> Sequence[Task]:
        return self.repository.find_by_status_id(status_id)

    def assign_task(self, task: Task, user: User) -> Task:
        task.user_id = user.id
        return self.repository.save(task)

    def move_task(self, task_id: int, status_id: int, previous_sibling_id: int, next_sibling_id: int) -> Task:
        """
        Updates the task with the given task_id
        :param task_id: the id of the task
        :param status_id: the id of the status of the task
        :param previous_sibling_id: the id of the previous sibling of the task
        :param next_sibling_id: the id of the next sibling of the task
        :return: the updated task
        """
        status = self.statuses_service.get_status(status_id)
        task = self.repository.find_by_id(task_id)

        if status.name == "done":
            updated_system_card = self.system_card_service.update(task.title)
            # TODO: change with task.conclusion if datamodel is changed
            self.storage_service.write(updated_system_card)

        # assign the task to the current user
        if status.name == "in_progress":
            task.user_id = 1

        # update the status for the task (this may not be needed if the status has not changed)
        task.status_id = status_id

        # update order position of the card
        if not previous_sibling_id and not next_sibling_id:
            task.sort_order = 10
        elif previous_sibling_id and next_sibling_id:
            previous_task = self.repository.find_by_id(previous_sibling_id)
            next_task = self.repository.find_by_id(next_sibling_id)
            new_sort_order = previous_task.sort_order + ((next_task.sort_order - previous_task.sort_order) / 2)
            task.sort_order = new_sort_order
        elif previous_sibling_id and not next_sibling_id:
            previous_task = self.repository.find_by_id(previous_sibling_id)
            task.sort_order = previous_task.sort_order + 10
        elif not previous_sibling_id and next_sibling_id:
            next_task = self.repository.find_by_id(next_sibling_id)
            task.sort_order = next_task.sort_order / 2

        return self.repository.save(task)