import pytest
from tad.core.exceptions import RepositoryError
from tad.models import Status
from tad.repositories.statuses import StatusesRepository
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

    assert result.id == 1
    assert result.name == "test"
    assert result.sort_order == 10


def test_save_failed(db: DatabaseTestUtils):
    status_repository: StatusesRepository = StatusesRepository(db.get_session())
    status: Status = Status(id=1, name="test", sort_order=10)
    status_repository.save(status)
    status: Status = Status(id=1, name="test has duplicate id", sort_order=10)
    with pytest.raises(RepositoryError):
        status_repository.save(status)


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
