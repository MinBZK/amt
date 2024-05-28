from collections.abc import Sequence
from unittest.mock import patch

import pytest
from tad.models import Status, Task, User
from tad.repositories.statuses import StatusesRepository
from tad.repositories.tasks import TasksRepository
from tad.services.statuses import StatusesService
from tad.services.tasks import TasksService


class MockStatusesRepository:
    def __init__(self):
        self._statuses = []
        self.reset()

    def reset(self):
        self._statuses.append(Status(id=1, name="todo", sort_order=1))
        self._statuses.append(Status(id=2, name="in_progress", sort_order=1))
        self._statuses.append(Status(id=3, name="review", sort_order=1))
        self._statuses.append(Status(id=4, name="done", sort_order=1))

    def find_by_id(self, status_id: int) -> Status:
        return next(filter(lambda x: x.id == status_id, self._statuses))


class MockTasksRepository:
    def __init__(self):
        self._tasks = []
        self.reset()

    def reset(self):
        self._tasks.append(Task(id=1, title="Test 1", description="Description 1", status_id=1, sort_order=10))
        self._tasks.append(Task(id=2, title="Test 2", description="Description 2", status_id=1, sort_order=20))
        self._tasks.append(Task(id=3, title="Test 3", description="Description 3", status_id=1, sort_order=30))
        self._tasks.append(Task(id=4, title="Test 4", description="Description 4", status_id=2, sort_order=10))
        self._tasks.append(Task(id=5, title="Test 5", description="Description 5", status_id=3, sort_order=20))

    def find_all(self):
        return self._tasks

    def find_by_status_id(self, status_id: int) -> Sequence[Task]:
        return list(filter(lambda x: x.status_id == status_id, self._tasks))

    def find_by_id(self, task_id: int) -> Task:
        return next(filter(lambda x: x.id == task_id, self._tasks))

    def save(self, task: Task) -> Task:
        pass  # objects are saved implicit because, there is no real repository


@pytest.fixture(scope="module")
def mock_tasks_repository():
    with patch("tad.services.tasks.TasksRepository"):
        mock_tasks_repository = MockTasksRepository()
        yield mock_tasks_repository


@pytest.fixture(scope="module")
def mock_statuses_repository():
    with patch("tad.services.statuses.StatusesRepository"):
        mock_statuses_repository = MockStatusesRepository()
        yield mock_statuses_repository


@pytest.fixture(scope="module")
def tasks_service_with_mock(mock_tasks_repository: TasksRepository, mock_statuses_repository: StatusesRepository):
    statuses_service = StatusesService(mock_statuses_repository)
    tasks_service = TasksService(statuses_service, mock_tasks_repository)
    return tasks_service


def test_get_tasks(tasks_service_with_mock, mock_tasks_repository):
    assert len(tasks_service_with_mock.get_tasks(1)) == 3


def test_assign_task(tasks_service_with_mock, mock_tasks_repository):
    task1: Task = mock_tasks_repository.find_by_id(1)
    user1: User = User(id=1)
    tasks_service_with_mock.assign_task(task1, user1)
    assert task1.user_id == 1


def test_move_task(tasks_service_with_mock, mock_tasks_repository):
    # test changing order
    mock_tasks_repository.reset()
    assert mock_tasks_repository.find_by_id(1).sort_order == 10
    tasks_service_with_mock.move_task(1, 1, 2, 3)
    assert mock_tasks_repository.find_by_id(1).sort_order == 25

    # test changing order
    mock_tasks_repository.reset()
    tasks_service_with_mock.move_task(1, 1, 3, None)
    assert mock_tasks_repository.find_by_id(1).sort_order == 40

    # test moving to in progress
    mock_tasks_repository.reset()
    mock_tasks_repository.find_by_id(1).sort_order = 0
    tasks_service_with_mock.move_task(1, 2, 0, 0)
    assert mock_tasks_repository.find_by_id(1).sort_order == 10
    assert mock_tasks_repository.find_by_id(1).user_id == 1

    # test moving to todo
    mock_tasks_repository.reset()
    mock_tasks_repository.find_by_id(1).sort_order = 0
    tasks_service_with_mock.move_task(1, 4, 0, 0)
    assert mock_tasks_repository.find_by_id(1).sort_order == 10

    # test moving move under other card
    mock_tasks_repository.reset()
    mock_tasks_repository.find_by_id(2).sort_order = 10
    tasks_service_with_mock.move_task(2, 1, 0, 1)
    assert mock_tasks_repository.find_by_id(2).sort_order == 5
