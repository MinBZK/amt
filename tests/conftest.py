from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel
from tad.core.config import settings
from tad.core.db import get_engine
from tad.main import app
from tad.repositories.statuses import StatusesRepository
from tad.repositories.tasks import TasksRepository
from tad.services.statuses import StatusesService
from tad.services.tasks import TasksService


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    # todo (robbert) creating an in memory database does not work right, tables seem to get lost?
    settings.APP_DATABASE_FILE = "database.sqlite3.test"  # set to none so we'll use an in memory database
    # todo (robbert) this seems to be the only way to get the right session object (but I am not sure why)
    with Session(get_engine()) as session:
        tasks_repository = TasksRepository(session=session)
        statuses_repository = StatusesRepository(session=session)
        statuses_service = StatusesService(repository=statuses_repository)
        tasks_service = TasksService(statuses_service=statuses_service, repository=tasks_repository)
        tasks_service.get_tasks(1)  # noop to test all object creations
        statuses_repository.create_example_statuses()
        tasks_repository.create_example_tasks()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app, raise_server_exceptions=True) as c:
        SQLModel.metadata.create_all(get_engine())
        c.timeout = 5
        yield c
