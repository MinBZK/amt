from collections.abc import Generator, Sequence
from typing import Any
from unittest.mock import patch

import pytest
from amt.models import Status
from amt.repositories.statuses import StatusesRepository
from amt.services.statuses import StatusesService


class MockStatusesRepository:
    def __init__(self) -> None:
        pass

    def find_by_id(self, status_id: int) -> Status:
        return Status(id=status_id, name="Test status", sort_order=1)

    def find_all(self) -> Sequence[Status]:
        return [self.find_by_id(1)]


@pytest.fixture(scope="module")
def mock_statuses_repository() -> Generator[MockStatusesRepository, Any, Any]:
    with patch("amt.services.statuses.StatusesRepository"):
        mock_statuses_repository = MockStatusesRepository()
        yield mock_statuses_repository


def test_get_status(mock_statuses_repository: StatusesRepository):
    statuses_service = StatusesService(mock_statuses_repository)
    status: Status = statuses_service.get_status(1)
    assert status.id == 1


def test_get_statuses(mock_statuses_repository: StatusesRepository):
    statuses_service = StatusesService(mock_statuses_repository)
    statuses = statuses_service.get_statuses()
    assert len(statuses) == 1
