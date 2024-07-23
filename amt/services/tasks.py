import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends

from amt.models.project import Project
from amt.models.task import Task
from amt.models.user import User
from amt.repositories.tasks import TasksRepository
from amt.schema.instrument import InstrumentTask
from amt.schema.system_card import SystemCard
from amt.services.statuses import StatusesService
from amt.services.storage import StorageFactory

logger = logging.getLogger(__name__)


class TasksService:
    def __init__(
        self,
        statuses_service: Annotated[StatusesService, Depends(StatusesService)],
        repository: Annotated[TasksRepository, Depends(TasksRepository)],
    ) -> None:
        self.repository = repository
        self.statuses_service = statuses_service
        self.storage_writer = StorageFactory.init(storage_type="file", location="./output", filename="system_card.yaml")
        self.system_card = SystemCard()

    def get_tasks(self, status_id: int) -> Sequence[Task]:
        return self.repository.find_by_status_id(status_id)

    def get_tasks_for_project(self, project_id: int, status_id: int) -> Sequence[Task]:
        return self.repository.find_by_project_id_and_status_id(project_id, status_id)

    def assign_task(self, task: Task, user: User) -> Task:
        task.user_id = user.id
        return self.repository.save(task)

    def create_instrument_tasks(self, tasks: Sequence[InstrumentTask], project: Project) -> None:
        # TODO: (Christopher) At this moment a status has to be retrieved from the DB. In the future
        #       we will have static statuses, so this will need to change.
        status = self.statuses_service.get_status_by_name("todo")
        self.repository.save_all(
            [
                # TODO: (Christopher) The ticket does not specify what to do when question type is not an
                # open questions, hence for now all titles will be set to task.question.
                Task(title=task.question, description="", project_id=project.id, status_id=status.id, sort_order=idx)
                for idx, task in enumerate(tasks)
            ]
        )

    def move_task(
        self, task_id: int, status_id: int, previous_sibling_id: int | None = None, next_sibling_id: int | None = None
    ) -> Task:
        """
        Updates the task with the given task_id
        :param task_id: the id of the task
        :param status_id: the id of the status of the task
        :param previous_sibling_id: the id of the previous sibling of the task or None
        :param next_sibling_id: the id of the next sibling of the task or None
        :return: the updated task
        """
        status = self.statuses_service.get_status(status_id)
        task = self.repository.find_by_id(task_id)

        if status.name == "done":
            self.system_card.name = task.title
            self.storage_writer.write(self.system_card.model_dump())

        if not isinstance(status.id, int):
            raise TypeError("status_id must be an integer")  # pragma: no cover

        # assign the task to the current user
        if status.id > 1:
            task.user_id = 1

        # update the status for the task (this may not be needed if the status has not changed)
        task.status_id = status_id

        # update order position of the card
        if previous_sibling_id and next_sibling_id:
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
        else:
            task.sort_order = 10

        return self.repository.save(task)
