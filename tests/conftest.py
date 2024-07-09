import os
from collections.abc import Callable, Generator, Iterator
from multiprocessing import Process
from typing import Any

import httpx
import pytest
from amt.core.config import Settings, get_settings
from amt.core.db import get_engine
from amt.server import app
from fastapi.testclient import TestClient
from playwright.sync_api import Browser
from sqlmodel import Session, SQLModel
from uvicorn.main import run as uvicorn_run

from tests.database_test_utils import DatabaseTestUtils


def run_uvicorn(host: str = "127.0.0.1", port: int = 3462) -> None:
    uvicorn_run(app, host=host, port=port)


@pytest.fixture(scope="session")
def run_server() -> Generator[Any, None, None]:
    process = Process(target=run_uvicorn)
    process.start()
    yield "http://127.0.0.1:3462"
    process.terminate()


@pytest.fixture()
def get_session() -> Generator[Session, Any, Any]:
    with Session(get_engine(), expire_on_commit=False) as session:
        yield session


def pytest_configure(config: pytest.Config) -> None:
    os.environ.clear()  # lets always start with a clean environment to make tests consistent
    os.environ["ENVIRONMENT"] = "local"
    os.environ["APP_DATABASE_SCHEME"] = "sqlite"


def pytest_sessionstart(session: pytest.Session) -> None:
    get_settings.cache_clear()
    get_engine.cache_clear()
    SQLModel.metadata.create_all(get_engine())


def pytest_sessionfinish(session: pytest.Session) -> None:
    SQLModel.metadata.drop_all(get_engine())


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app, raise_server_exceptions=True) as c:
        # app.dependency_overrides[get_app_session] = get_session  # noqa: ERA001
        c.timeout = 5
        yield c


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    return {**browser_context_args, "base_url": "http://127.0.0.1:3462"}


@pytest.fixture(scope="session")
def browser(
    launch_browser: Callable[[], Browser], run_server: Generator[str, None, None]
) -> Generator[Browser, None, None]:
    transport = httpx.HTTPTransport(retries=10, local_address="127.0.0.1")
    with httpx.Client(transport=transport, verify=False, timeout=1.0) as client:  # noqa: S501
        client.get(f"{run_server}/")

    browser = launch_browser()
    yield browser
    browser.close()


@pytest.fixture()
def db(get_session: Session) -> Generator[DatabaseTestUtils, None, None]:
    database = DatabaseTestUtils(get_session)
    yield database
    del database


@pytest.fixture()
def patch_settings(request: pytest.FixtureRequest) -> Iterator[Settings]:
    settings = get_settings()
    original_settings = settings.model_copy()

    vars_to_patch = getattr(request, "param", {})

    for k, v in settings.model_fields.items():
        setattr(settings, k, v.default)

    for key, val in vars_to_patch.items():
        if not hasattr(settings, key):
            raise ValueError(f"Unknown setting: {key}")

        # Raise an error if the env var has an invalid type
        expected_type = getattr(settings, key).__class__
        if not isinstance(val, expected_type):
            raise ValueError(f"Invalid type for {key}: {val.__class__} instead " "of {expected_type}")  # noqa: TRY004
        setattr(settings, key, val)

    yield settings

    # Restore the original settings
    settings.__dict__.update(original_settings.__dict__)
