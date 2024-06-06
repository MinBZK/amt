import pytest
from sqlmodel import Session
from tad.core.exceptions import RepositoryError
from tad.models import Task
from tad.repositories.tasks import TasksRepository
from tests.database_test_utils import DatabaseTestUtils


def test_find_all(get_session: Session, db: DatabaseTestUtils):
    db.init(
        [
            {"table": "task", "id": 1, "status_id": 1},
            {"table": "task", "id": 2, "status_id": 1},
        ]
    )
    tasks_repository: TasksRepository = TasksRepository(get_session)
    results = tasks_repository.find_all()
    assert results[0].id == 1
    assert results[1].id == 2
    assert len(results) == 2


def test_find_all_no_results(get_session: Session, db: DatabaseTestUtils):
    db.init()
    tasks_repository: TasksRepository = TasksRepository(get_session)
    results = tasks_repository.find_all()
    assert len(results) == 0


def test_save(get_session: Session, db: DatabaseTestUtils):
    db.init()
    tasks_repository: TasksRepository = TasksRepository(get_session)
    task: Task = Task(id=1, title="Test title", description="Test description", sort_order=10)
    tasks_repository.save(task)
    result = db.get_items({"table": "task", "id": 1})
    assert result[0].id == 1
    assert result[0].title == "Test title"
    assert result[0].description == "Test description"
    assert result[0].sort_order == 10


@pytest.mark.filterwarnings("ignore:New instance")
def test_save_failed(get_session: Session, db: DatabaseTestUtils):
    db.init()
    tasks_repository: TasksRepository = TasksRepository(get_session)
    task: Task = Task(id=1, title="Test title", description="Test description", sort_order=10)
    tasks_repository.save(task)
    task_duplicate: Task = Task(id=1, title="Test title duplicate", description="Test description", sort_order=10)
    with pytest.raises(RepositoryError):
        tasks_repository.save(task_duplicate)


def test_find_by_id(get_session: Session, db: DatabaseTestUtils):
    db.init([{"table": "task", "id": 1, "title": "test for find by id"}])
    tasks_repository: TasksRepository = TasksRepository(get_session)
    result: Task = tasks_repository.find_by_id(1)
    assert result.id == 1
    assert result.title == "test for find by id"


def test_find_by_id_failed(get_session: Session, db: DatabaseTestUtils):
    db.init()
    tasks_repository: TasksRepository = TasksRepository(get_session)
    with pytest.raises(RepositoryError):
        tasks_repository.find_by_id(1)


def test_find_by_status_id(get_session: Session, db: DatabaseTestUtils):
    db.init(
        [
            {"table": "status", "id": 1},
            {"table": "task", "id": 1, "status_id": 1},
            {"table": "task", "id": 2, "status_id": 1},
        ]
    )
    tasks_repository: TasksRepository = TasksRepository(get_session)
    results = tasks_repository.find_by_status_id(1)
    assert len(results) == 2
    assert results[0].id == 1
    assert results[1].id == 2
