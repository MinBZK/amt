import logging

from tad.core.singleton import Singleton
from tad.models.task import Task
from tad.models.user import User
from tad.repositories.tasks import TasksRepository
from tad.services.statuses import StatusesService

logger = logging.getLogger(__name__)


class TasksService(metaclass=Singleton):
    __tasks_repository = TasksRepository()
    __statuses_service = StatusesService()

    def __init__(self):
        pass

    def get_tasks(self, status_id):
        return self.__tasks_repository.find_by_status_id(status_id)

    def assign_task(self, task: Task, user: User):
        task.user_id = user.id
        self.__tasks_repository.save(task)

    def move_task(self, task_id, status_id, previous_sibling_id, next_sibling_id) -> Task:
        status = self.__statuses_service.get_status(status_id)
        task = self.__tasks_repository.find_by_id(task_id)

        if status.name == "done":
            # TODO implement logic for done
            logging.warning("Task is done, we need to update a system card")

        # assign the task to the current user
        if status.name == "in_progress":
            task.user_id = 1

        # update the status for the task (this may not be needed if the status has not changed)
        task.status_id = status_id

        # update order position of the card
        if not previous_sibling_id and not next_sibling_id:
            task.sort_order = 10
        elif previous_sibling_id and next_sibling_id:
            previous_task = self.__tasks_repository.find_by_id(int(previous_sibling_id))
            next_task = self.__tasks_repository.find_by_id(int(next_sibling_id))
            new_sort_order = previous_task.sort_order + ((next_task.sort_order - previous_task.sort_order) / 2)
            task.sort_order = new_sort_order
        elif previous_sibling_id and not next_sibling_id:
            previous_task = self.__tasks_repository.find_by_id(int(previous_sibling_id))
            task.sort_order = previous_task.sort_order + 10
        elif not previous_sibling_id and next_sibling_id:
            next_task = self.__tasks_repository.find_by_id(int(next_sibling_id))
            task.sort_order = next_task.sort_order / 2

        task = self.__tasks_repository.save(task)

        return task
