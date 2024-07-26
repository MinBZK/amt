from collections.abc import Sequence
from pathlib import Path
from unittest.mock import patch

import pytest
from amt.models import Task, User
from amt.models.project import Project
from amt.repositories.tasks import TasksRepository
from amt.schema.instrument import InstrumentTask
from amt.services.tasks import TasksService


class MockTasksRepository:
    def __init__(self) -> None:
        self._tasks: list[Task] = []
        self.reset()

    def clear(self) -> None:
        self._tasks.clear()

    def reset(self):
        self.clear()
        self._tasks.append(
            Task(id=1, title="Test 1", description="Description 1", status_id=1, project_id=1, sort_order=10)
        )
        self._tasks.append(
            Task(id=2, title="Test 2", description="Description 2", status_id=1, project_id=1, sort_order=20)
        )
        self._tasks.append(
            Task(id=3, title="Test 3", description="Description 3", status_id=1, project_id=2, sort_order=30)
        )
        self._tasks.append(
            Task(id=4, title="Test 4", description="Description 4", status_id=2, project_id=1, sort_order=10)
        )
        self._tasks.append(
            Task(id=5, title="Test 5", description="Description 5", status_id=3, project_id=3, sort_order=20)
        )

    def find_all(self):
        return self._tasks

    def find_by_status_id(self, status_id: int) -> Sequence[Task]:
        return list(filter(lambda x: x.status_id == status_id, self._tasks))

    def find_by_project_id_and_status_id(self, project_id: int, status_id: int) -> Sequence[Task]:
        return list(filter(lambda x: x.status_id == status_id and x.project_id == project_id, self._tasks))

    def find_by_id(self, task_id: int) -> Task:
        return next(filter(lambda x: x.id == task_id, self._tasks))

    def save(self, task: Task) -> Task:
        return task

    def save_all(self, tasks: Sequence[Task]) -> None:
        for task in tasks:
            self._tasks.append(task)
        return None


@pytest.fixture(scope="module")
def mock_tasks_repository():
    with patch("amt.services.tasks.TasksRepository"):
        mock_tasks_repository = MockTasksRepository()
        yield mock_tasks_repository


@pytest.fixture(scope="module")
def tasks_service_with_mock(mock_tasks_repository: TasksRepository):
    tasks_service = TasksService(mock_tasks_repository)
    return tasks_service


def test_get_tasks(tasks_service_with_mock: TasksService, mock_tasks_repository: TasksRepository):
    assert len(tasks_service_with_mock.get_tasks(1)) == 3


def test_get_tasks_for_project(tasks_service_with_mock: TasksService, mock_tasks_repository: TasksRepository):
    assert len(tasks_service_with_mock.get_tasks_for_project(1, 1)) == 2


def test_assign_task(tasks_service_with_mock: TasksService, mock_tasks_repository: TasksRepository):
    task1: Task = mock_tasks_repository.find_by_id(1)
    user1: User = User(id=1, name="User 1", avatar="none.jpg")
    tasks_service_with_mock.assign_task(task1, user1)
    assert task1.user_id == 1


def test_create_instrument_tasks(tasks_service_with_mock: TasksService, mock_tasks_repository: MockTasksRepository):
    # Given
    task_1 = InstrumentTask(question="question_1", urn="instrument_1_task_1", lifecycle=[])
    task_2 = InstrumentTask(question="question_1", urn="instrument_1_task_1", lifecycle=[])

    project_id = 1
    project_name = "Project 1"
    project_model_card = Path("model_card_path")
    project = Project(id=project_id, name=project_name, model_card=str(project_model_card))

    # When
    mock_tasks_repository.clear()
    tasks_service_with_mock.create_instrument_tasks([task_1, task_2], project)

    # Then
    assert len(mock_tasks_repository.find_all()) == 2
    assert mock_tasks_repository.find_all()[0].project_id == 1
    assert mock_tasks_repository.find_all()[0].title == task_1.question
    assert mock_tasks_repository.find_all()[1].project_id == 1
    assert mock_tasks_repository.find_all()[1].title == task_2.question


def test_move_task(tasks_service_with_mock: TasksService, mock_tasks_repository: MockTasksRepository):
    # test changing order between 2 cards
    mock_tasks_repository.reset()
    assert mock_tasks_repository.find_by_id(1).sort_order == 10
    tasks_service_with_mock.move_task(1, 1, 2, 3)
    assert mock_tasks_repository.find_by_id(1).sort_order == 25

    # test changing order, after the last card
    mock_tasks_repository.reset()
    tasks_service_with_mock.move_task(1, 1, 3, None)
    assert mock_tasks_repository.find_by_id(1).sort_order == 40

    # test changing order, before the first card
    mock_tasks_repository.reset()
    assert mock_tasks_repository.find_by_id(3).sort_order == 30
    tasks_service_with_mock.move_task(3, 1, None, 1)
    assert mock_tasks_repository.find_by_id(3).sort_order == 5

    # test moving to in progress
    mock_tasks_repository.reset()
    mock_tasks_repository.find_by_id(1).sort_order = 0
    tasks_service_with_mock.move_task(1, 2)
    assert mock_tasks_repository.find_by_id(1).sort_order == 10
    assert mock_tasks_repository.find_by_id(1).user_id == 1

    # test moving to todo
    mock_tasks_repository.reset()
    mock_tasks_repository.find_by_id(1).sort_order = 0
    tasks_service_with_mock.move_task(1, 4)
    assert mock_tasks_repository.find_by_id(1).sort_order == 10

    # test moving move under other card
    mock_tasks_repository.reset()
    mock_tasks_repository.find_by_id(2).sort_order = 10
    tasks_service_with_mock.move_task(2, 1, None, 1)
    assert mock_tasks_repository.find_by_id(2).sort_order == 5
