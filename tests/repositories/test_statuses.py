import pytest
from sqlmodel import Session
from tad.models import Status
from tad.repositories.exceptions import RepositoryError
from tad.repositories.statuses import StatusesRepository
from tests.database_test_utils import get_items, init_db


def test_find_all(get_session: Session):
    init_db(
        [
            {"table": "status", "id": 1},
            {"table": "status", "id": 2},
        ]
    )
    status_repository: StatusesRepository = StatusesRepository(get_session)
    results = status_repository.find_all()
    assert results[0].id == 1
    assert results[1].id == 2
    assert len(results) == 2


def test_save(get_session: Session):
    init_db()
    status_repository: StatusesRepository = StatusesRepository(get_session)
    status: Status = Status(id=1, name="test", sort_order=10)
    status_repository.save(status)
    result = get_items({"table": "status", "id": 1})
    assert result[0].id == 1
    assert result[0].name == "test"
    assert result[0].sort_order == 10


def test_save_failed(get_session: Session):
    init_db()
    status_repository: StatusesRepository = StatusesRepository(get_session)
    status: Status = Status(id=1, name="test", sort_order=10)
    status_repository.save(status)
    status: Status = Status(id=1, name="test has duplicate id", sort_order=10)
    with pytest.raises(RepositoryError):
        status_repository.save(status)


def test_find_by_id(get_session: Session):
    init_db([{"table": "status", "id": 1, "name": "test for find by id"}])
    status_repository: StatusesRepository = StatusesRepository(get_session)
    result: Status = status_repository.find_by_id(1)
    assert result.id == 1
    assert result.name == "test for find by id"


def test_find_by_id_failed(get_session: Session):
    init_db()
    status_repository: StatusesRepository = StatusesRepository(get_session)
    with pytest.raises(RepositoryError):
        status_repository.find_by_id(1)
