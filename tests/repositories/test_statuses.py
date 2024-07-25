import pytest
from amt.core.exceptions import RepositoryError
from amt.models import Status
from amt.repositories.statuses import StatusesRepository
from tests.constants import in_progress_status, todo_status
from tests.database_test_utils import DatabaseTestUtils


def test_find_all(db: DatabaseTestUtils):
    db.given([todo_status(), in_progress_status()])
    status_repository: StatusesRepository = StatusesRepository(db.get_session())
    results = status_repository.find_all()
    assert results[0].id == 1
    assert results[1].id == 2
    assert len(results) == 2


def test_find_all_no_results(db: DatabaseTestUtils):
    status_repository: StatusesRepository = StatusesRepository(db.get_session())
    results = status_repository.find_all()
    assert len(results) == 0


def test_save(db: DatabaseTestUtils):
    status_repository: StatusesRepository = StatusesRepository(db.get_session())
    status: Status = Status(id=1, name="test", sort_order=10)
    status_repository.save(status)

    result = status_repository.find_by_id(1)

    status_repository.delete(status)  # cleanup

    assert result.id == 1
    assert result.name == "test"
    assert result.sort_order == 10


def test_delete(db: DatabaseTestUtils):
    status_repository: StatusesRepository = StatusesRepository(db.get_session())
    status: Status = Status(id=1, name="test", sort_order=10)
    status_repository.save(status)
    status_repository.delete(status)

    results = status_repository.find_all()

    assert len(results) == 0


def test_save_failed(db: DatabaseTestUtils):
    status_repository: StatusesRepository = StatusesRepository(db.get_session())
    status: Status = Status(id=1, name="test", sort_order=10)
    status_duplicate: Status = Status(id=1, name="test has duplicate id", sort_order=10)

    status_repository.save(status)

    with pytest.raises(RepositoryError):
        status_repository.save(status_duplicate)

    status_repository.delete(status)  # cleanup


def test_delete_failed(db: DatabaseTestUtils):
    status_repository: StatusesRepository = StatusesRepository(db.get_session())
    status: Status = Status(id=1, name="test", sort_order=10)

    with pytest.raises(RepositoryError):
        status_repository.delete(status)


def test_find_by_id(db: DatabaseTestUtils):
    status = todo_status()
    db.given([status])

    status_repository: StatusesRepository = StatusesRepository(db.get_session())
    result: Status = status_repository.find_by_id(1)
    assert result.id == 1
    assert result.name == status.name


def test_find_by_id_failed(db: DatabaseTestUtils):
    status_repository: StatusesRepository = StatusesRepository(db.get_session())
    with pytest.raises(RepositoryError):
        status_repository.find_by_id(1)


def test_find_by_name(db: DatabaseTestUtils):
    status = todo_status()
    db.given([status])

    status_repository: StatusesRepository = StatusesRepository(db.get_session())
    result: Status = status_repository.find_by_name(status.name)
    assert result.id == 1
    assert result.name == status.name


def test_find_by_name_failed(db: DatabaseTestUtils):
    status_repository: StatusesRepository = StatusesRepository(db.get_session())
    with pytest.raises(RepositoryError):
        status_repository.find_by_name("test")
