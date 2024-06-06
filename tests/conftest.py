import os
from collections.abc import Generator, Iterator
from multiprocessing import Process
from typing import Any

import httpx
import pytest
from _pytest.fixtures import SubRequest
from fastapi.testclient import TestClient
from playwright.sync_api import Page, Playwright, sync_playwright
from sqlmodel import Session, SQLModel
from tad.core.config import Settings, get_settings
from tad.core.db import get_engine
from tad.main import app
from uvicorn.main import run as uvicorn_run

from tests.database_test_utils import DatabaseTestUtils


@pytest.fixture(scope="module")
def run_server(request: pytest.FixtureRequest) -> Generator[Any, None, None]:
    def run_uvicorn(uvicorn: Any) -> None:
        uvicorn_run(app, host=uvicorn["host"], port=uvicorn["port"])

    uvicorn_settings = request.config.uvicorn  # type: ignore

    process = Process(target=run_uvicorn, args=(uvicorn_settings,))  # type: ignore
    process.start()
    yield f"http://{uvicorn_settings['host']}:{uvicorn_settings['port']}"
    process.terminate()


@pytest.fixture()
def get_session() -> Generator[Session, Any, Any]:
    with Session(get_engine(), expire_on_commit=False) as session:
        yield session


def pytest_configure(config: pytest.Config) -> None:
    os.environ.clear()  # lets always start with a clean environment to make tests consistent
    os.environ["ENVIRONMENT"] = "local"
    os.environ["APP_DATABASE_SCHEME"] = "sqlite"

    config.uvicorn = {  # type: ignore
        "host": "localhost",
        "port": 8756,
    }


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


@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as p:
        yield p


@pytest.fixture(params=["chromium"])  # lets start with 1 browser for now, we can add more later
def browser(
    playwright: Playwright, request: SubRequest, run_server: Generator[str, Any, Any]
) -> Generator[Page, Any, Any]:
    browser = getattr(playwright, request.param).launch(headless=True)
    context = browser.new_context(base_url=run_server)
    page = context.new_page()

    transport = httpx.HTTPTransport(retries=5)
    with httpx.Client(transport=transport, verify=False) as client:  # noqa: S501
        client.get(f"{run_server}/", timeout=0.3)

    yield page
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
