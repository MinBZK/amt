import pytest
from amt.core.exceptions import RepositoryError
from amt.enums.status import Status
from amt.models import Task
from amt.repositories.tasks import TasksRepository
from tests.constants import default_project, default_task
from tests.database_test_utils import DatabaseTestUtils


def test_find_all(db: DatabaseTestUtils):
    db.given([default_task(), default_task()])

    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    results = tasks_repository.find_all()
    assert results[0].id == 1
    assert results[1].id == 2
    assert len(results) == 2


def test_find_all_no_results(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    results = tasks_repository.find_all()
    assert len(results) == 0


def test_save(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    task: Task = Task(id=1, title="Test title", description="Test description", sort_order=10)
    tasks_repository.save(task)
    result = tasks_repository.find_by_id(1)

    assert result.id == 1
    assert result.title == "Test title"
    assert result.description == "Test description"
    assert result.sort_order == 10

    tasks_repository.delete(task)  # cleanup


def test_save_all(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    task_1: Task = Task(id=1, title="Test title 1", description="Test description 1", sort_order=10)
    task_2: Task = Task(id=2, title="Test title 2", description="Test description 2", sort_order=11)
    tasks_repository.save_all([task_1, task_2])
    result_1 = tasks_repository.find_by_id(1)
    result_2 = tasks_repository.find_by_id(2)

    assert result_1.id == 1
    assert result_1.title == "Test title 1"
    assert result_1.description == "Test description 1"
    assert result_1.sort_order == 10

    assert result_2.id == 2
    assert result_2.title == "Test title 2"
    assert result_2.description == "Test description 2"
    assert result_2.sort_order == 11

    tasks_repository.delete(task_1)  # cleanup
    tasks_repository.delete(task_2)  # cleanup


def test_save_all_failed(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    task: Task = Task(id=1, title="Test title", description="Test description", sort_order=10)
    tasks_repository.save_all([task])
    task_duplicate: Task = Task(id=1, title="Test title duplicate", description="Test description", sort_order=10)
    with pytest.raises(RepositoryError):
        tasks_repository.save_all([task_duplicate])

    tasks_repository.delete(task)  # cleanup


def test_delete_task(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    task: Task = Task(id=1, title="Test title", description="Test description", sort_order=10)

    tasks_repository.save(task)
    tasks_repository.delete(task)  # cleanup

    results = tasks_repository.find_all()

    assert len(results) == 0


def test_save_failed(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    task: Task = Task(id=1, title="Test title", description="Test description", sort_order=10)
    tasks_repository.save(task)
    task_duplicate: Task = Task(id=1, title="Test title duplicate", description="Test description", sort_order=10)
    with pytest.raises(RepositoryError):
        tasks_repository.save(task_duplicate)

    tasks_repository.delete(task)  # cleanup


def test_delete_failed(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    task: Task = Task(id=1, title="Test title", description="Test description", sort_order=10)
    with pytest.raises(RepositoryError):
        tasks_repository.delete(task)


def test_find_by_id(db: DatabaseTestUtils):
    task = default_task()
    db.given([task])

    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    result: Task = tasks_repository.find_by_id(1)
    assert result.id == 1
    assert result.title == "Default Task"


def test_find_by_id_failed(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    with pytest.raises(RepositoryError):
        tasks_repository.find_by_id(1)


def test_find_by_status_id(db: DatabaseTestUtils):
    task = default_task(status_id=Status.TODO)
    db.given([task, default_task()])

    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    results = tasks_repository.find_by_status_id(1)
    assert len(results) == 1
    assert results[0].id == 1


def test_find_by_project_id_and_status_id(db: DatabaseTestUtils):
    db.given([default_project()])
    task = default_task(status_id=Status.TODO, project_id=1)
    db.given([task, default_task()])

    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    results = tasks_repository.find_by_project_id_and_status_id(1, 1)
    assert len(results) == 1
    assert results[0].id == 1
    assert results[0].project_id == 1
