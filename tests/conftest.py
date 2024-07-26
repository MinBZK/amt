import logging
import os
from collections.abc import Callable, Generator
from multiprocessing import Process
from pathlib import Path
from typing import Any

import httpx
import pytest
import uvicorn
from amt.models import *  # noqa
from amt.server import create_app
from fastapi.testclient import TestClient
from playwright.sync_api import Browser
from sqlmodel import Session, SQLModel, create_engine

from tests.database_e2e_setup import setup_database_e2e
from tests.database_test_utils import DatabaseTestUtils

logger = logging.getLogger(__name__)


def run_server_uvicorn(database_file: Path, host: str = "127.0.0.1", port: int = 3462) -> None:
    os.environ["APP_DATABASE_FILE"] = "/" + str(database_file)
    os.environ["AUTO_CREATE_SCHEMA"] = "true"
    logger.info(os.environ["APP_DATABASE_FILE"])
    app = create_app()
    uvicorn.run(app, host=host, port=port)


@pytest.fixture(scope="session")
def setup_db_and_server(tmp_path_factory: pytest.TempPathFactory) -> Generator[Any, None, None]:
    test_dir = tmp_path_factory.mktemp("e2e_database")
    database_file = test_dir / "test.sqlite3"
    engine = create_engine(f"sqlite:///{database_file}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        setup_database_e2e(session)

    process = Process(target=run_server_uvicorn, args=(database_file,))
    process.start()
    yield "http://127.0.0.1:3462"
    process.terminate()


def pytest_configure(config: pytest.Config) -> None:
    os.environ.clear()  # lets always start with a clean environment to make tests consistent
    os.environ["ENVIRONMENT"] = "local"
    os.environ["APP_DATABASE_SCHEME"] = "sqlite"


def pytest_collection_modifyitems(session: pytest.Session, config: pytest.Config, items: list[pytest.Item]):
    # this hook into pytest makes sure that the e2e tests are run last
    e2e_tests: list[pytest.Item] = []
    tests: list[pytest.Item] = []

    for item in items:
        if item.location[0].startswith("tests/e2e") or item.location[0].startswith("tests/regression"):
            e2e_tests.append(item)
        else:
            tests.append(item)

    e2e_tests.sort(key=lambda item: item.name)

    logger.info("e2e test order:")
    for item in e2e_tests:
        logger.info(item.name)

    items[:] = tests + e2e_tests


@pytest.fixture()
def client(db: DatabaseTestUtils, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    # overwrite db url
    monkeypatch.setenv("APP_DATABASE_FILE", "/" + str(db.get_database_file()))
    from amt.repositories.deps import get_session

    app = create_app()

    with TestClient(app, raise_server_exceptions=True) as c:
        app.dependency_overrides[get_session] = db.get_session
        c.timeout = 5
        yield c


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    return {**browser_context_args, "base_url": "http://127.0.0.1:3462"}


@pytest.fixture(scope="session")
def browser(
    launch_browser: Callable[[], Browser], setup_db_and_server: Generator[str, None, None]
) -> Generator[Browser, None, None]:
    transport = httpx.HTTPTransport(retries=5)
    with httpx.Client(transport=transport, verify=False, timeout=0.7) as client:  # noqa: S501
        client.get(f"{setup_db_and_server}/")

    browser = launch_browser()
    yield browser
    browser.close()


@pytest.fixture()
def db(tmp_path: Path) -> Generator[DatabaseTestUtils, None, None]:
    database_file = tmp_path / "test.sqlite3"
    engine = create_engine(f"sqlite:///{database_file}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        yield DatabaseTestUtils(session, database_file)
