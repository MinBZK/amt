import logging
import os
import re
from collections.abc import Callable, Generator
from multiprocessing import Process
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
import uvicorn
from amt.models.base import Base
from amt.server import create_app
from fastapi.testclient import TestClient
from fastapi_csrf_protect import CsrfProtect  # type: ignore
from playwright.sync_api import Browser
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from tests.database_e2e_setup import setup_database_e2e
from tests.database_test_utils import DatabaseTestUtils

logger = logging.getLogger(__name__)


def run_server_uvicorn(database_file: Path, host: str = "127.0.0.1", port: int = 3462) -> None:
    os.environ["APP_DATABASE_FILE"] = "/" + str(database_file)
    os.environ["AUTO_CREATE_SCHEMA"] = "true"
    os.environ["DISABLE_AUTH"] = "true"
    logger.info(os.environ["APP_DATABASE_FILE"])
    app = create_app()
    uvicorn.run(app, host=host, port=port)


@pytest.fixture(scope="session")
def setup_db_and_server(
    tmp_path_factory: pytest.TempPathFactory, request: pytest.FixtureRequest
) -> Generator[Any, None, None]:
    test_dir = tmp_path_factory.mktemp("e2e_database")
    database_file = test_dir / "test.sqlite3"

    if request.config.getoption("--db") == "postgresql":
        engine = create_engine(get_db_uri())
    else:
        engine = create_engine(f"sqlite:///{database_file}", connect_args={"check_same_thread": False})
    metadata = Base.metadata
    metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        setup_database_e2e(session)

    process = Process(target=run_server_uvicorn, args=(database_file,))
    process.start()
    yield "http://127.0.0.1:3462"
    process.terminate()
    metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def disable_auth(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: PT004
    marker = request.node.get_closest_marker("enable_auth")  # type: ignore
    if not marker:
        monkeypatch.setenv("DISABLE_AUTH", "true")
    return


def pytest_configure(config: pytest.Config) -> None:
    if "APP_DATABASE_SCHEME" not in os.environ:
        os.environ["APP_DATABASE_SCHEME"] = str(config.getoption("--db"))


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--db", action="store", default="sqlite", help="db: sqlite or postgresql", choices=("sqlite", "postgresql")
    )


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


@pytest.fixture
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


def get_db_uri() -> str:
    user = os.getenv("APP_DATABASE_USER", "amt")
    password = os.getenv("APP_DATABASE_PASSWORD", "changethis")
    server = os.getenv("APP_DATABASE_SERVER", "db")
    port = os.getenv("APP_DATABASE_PORT", "5432")
    db = os.getenv("APP_DATABASE_DB", "amt")
    return f"postgresql://{user}:{password}@{server}:{port}/{db}"


def create_db(new_db: str) -> str:
    url = get_db_uri()
    engine = create_engine(url, isolation_level="AUTOCOMMIT")

    if new_db == os.getenv("APP_DATABASE_USER", "amt"):
        return url

    logger.info(f"Creating database {new_db}")
    user = os.getenv("APP_DATABASE_USER", "amt")
    with Session(engine) as session:
        session.execute(text(f"DROP DATABASE IF EXISTS {new_db};"))  # type: ignore
        session.execute(text(f"CREATE DATABASE {new_db} OWNER {user};"))  # type: ignore
        session.commit()

    path = Path(url)

    return str(path.parent / new_db).replace("postgresql:/", "postgresql://")


def generate_db_name(request: pytest.FixtureRequest) -> str:
    pattern = re.compile(r"[^a-zA-Z0-9_]")

    inverted_modulename = ".".join(request.module.__name__.split(".")[::-1])  # type: ignore
    testname = request.node.name  # type: ignore

    db_name = testname + "_" + inverted_modulename  # type: ignore
    sanitized_name = pattern.sub("_", db_name)  # type: ignore

    # postgres has a limit of 63 bytes for database names
    if len(sanitized_name) > 63:
        sanitized_name = sanitized_name[:63]

    return sanitized_name


@pytest.fixture
def db(
    tmp_path: Path, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Generator[DatabaseTestUtils, None, None]:
    database_file = tmp_path / "test.sqlite3"

    if request.config.getoption("--db") == "postgresql":
        db_name: str = generate_db_name(request)
        url = create_db(db_name)
        monkeypatch.setenv("APP_DATABASE_DB", db_name)
        engine = create_engine(url)
    else:
        engine = create_engine(f"sqlite:///{database_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        yield DatabaseTestUtils(session, database_file)
