import pytest
from tad.core.exceptions import RepositoryError
from tad.models import Task
from tad.repositories.tasks import TasksRepository
from tests.constants import all_statusses, default_task
from tests.database_test_utils import DatabaseTestUtils


def test_find_all(db: DatabaseTestUtils):
    db.given([*all_statusses()])
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


def test_delete(db: DatabaseTestUtils):
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
    db.given([*all_statusses()])
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
    all_status = [*all_statusses()]
    db.given([*all_status])
    task = default_task(status_id=all_status[0].id)
    db.given([task, default_task()])

    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    results = tasks_repository.find_by_status_id(1)
    assert len(results) == 1
    assert results[0].id == 1
