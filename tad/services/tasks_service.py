from tad.models.status import Status
from tad.models.task import Task
from tad.models.user import User


class TasksService:
    _self = None
    _statuses = list[Status]
    _tasks = list[Task]

    # make sure this is a singleton class, this may not be needed?
    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def __init__(self):
        # this is dummy data to get started, this should be retrieved from the database
        # TODO all status and task retrieval should be database calls
        self._statuses = []
        self._statuses.append(Status(id=1, name="todo", sort_order=1))
        self._statuses.append(Status(id=2, name="in_progress", sort_order=2))
        self._statuses.append(Status(id=3, name="review", sort_order=3))
        self._statuses.append(Status(id=4, name="done", sort_order=4))

        self._tasks = []
        self._tasks.append(
            Task(
                id=1,
                status_id=1,
                title="IAMA",
                description="Impact Assessment Mensenrechten en Algoritmes",
                sort_order=10,
            )
        )
        self._tasks.append(Task(id=2, status_id=1, title="SHAP", description="SHAP", sort_order=20))
        self._tasks.append(
            Task(id=3, status_id=1, title="This is title 3", description="This is description 3", sort_order=30)
        )

    def _get_task_by_id(self, task_id: int) -> Task:
        return next(task for task in self._tasks if task.id == task_id)

    def _get_status_by_id(self, status_id: int) -> Status:
        return next(status for status in self._statuses if status.id == status_id)

    def get_statuses(self) -> []:
        return self._statuses

    def get_tasks(self, status_id):
        # TODO lines below probably can be simplified / combined
        res = [val for val in self._tasks if val.status_id == status_id]
        sorted_res = sorted(res, key=lambda sort_task: sort_task.sort_order)  # sort by age
        return sorted_res

    def assign_task(self, task: Task, user: User):
        task.user_id = user.id
        # TODO persist to database and / or decided when to persist (combined calls)

    def get_status(self, status_id) -> Status:
        return self._get_status_by_id(status_id)

    def get_task(self, task_id) -> Task:
        return self._get_task_by_id(task_id)

    def move_task(self, task_id, status_id, previous_sibling_id, next_sibling_id) -> Task:
        status = self.get_status(status_id)
        task = self.get_task(task_id)

        # assign the task to the current user
        if status.name == "in_progress":
            task.user_id = 1

        # update the status for the task (this may not be needed if the status has not changed)
        task.status_id = status_id

        # update order position of the card
        if not previous_sibling_id and not next_sibling_id:
            task.sort_order = 10
        elif previous_sibling_id and next_sibling_id:
            previous_task = self.get_task(previous_sibling_id)
            next_task = self.get_task(next_sibling_id)
            new_sort_order = previous_task.sort_order + ((next_task.sort_order - previous_task.sort_order) / 2)
            task.sort_order = new_sort_order
        elif previous_sibling_id and not next_sibling_id:
            previous_task = self.get_task(previous_sibling_id)
            task.sort_order = previous_task.sort_order + 10
        elif not previous_sibling_id and next_sibling_id:
            next_task = self.get_task(next_sibling_id)
            task.sort_order = next_task.sort_order / 2
        return task
