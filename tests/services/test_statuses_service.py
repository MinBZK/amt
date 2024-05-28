from collections.abc import Sequence
from unittest.mock import patch

import pytest
from tad.models import Status
from tad.services.statuses import StatusesService


class MockStatusesRepository:
    def __init__(self):
        pass

    def find_by_id(self, status_id: int) -> Status:
        return Status(id=status_id)

    def find_all(self) -> Sequence[Status]:
        return [self.find_by_id(1)]


@pytest.fixture(scope="module")
def mock_statuses_repository():
    with patch("tad.services.statuses.StatusesRepository"):
        mock_statuses_repository = MockStatusesRepository()
        yield mock_statuses_repository


def test_get_status(mock_statuses_repository):
    statuses_service = StatusesService(mock_statuses_repository)
    status: Status = statuses_service.get_status(1)
    assert status.id == 1


def test_get_statuses(mock_statuses_repository):
    statuses_service = StatusesService(mock_statuses_repository)
    statuses = statuses_service.get_statuses()
    assert len(statuses) == 1
