import os
import urllib
from collections.abc import Generator
from multiprocessing import Process
from time import sleep
from typing import Any
from urllib.error import URLError

import pytest
import uvicorn
from _pytest.fixtures import SubRequest
from fastapi.testclient import TestClient
from playwright.sync_api import Page, Playwright, sync_playwright
from sqlmodel import Session
from tad.core.config import settings
from tad.core.db import get_engine
from tad.main import app

from tests.database_test_utils import DatabaseTestUtils


class TestSettings:
    HTTP_SERVER_SCHEME: str = "http://"
    HTTP_SERVER_HOST: str = "127.0.0.1"
    HTTP_SERVER_PORT: int = 8000
    TIME_OUT: int = 10


def run_server() -> None:
    uvicorn.run(app, host=TestSettings.HTTP_SERVER_HOST, port=TestSettings.HTTP_SERVER_PORT)


def wait_for_server_ready(server: Generator[Any, Any, Any]) -> None:
    for _ in range(TestSettings.TIME_OUT):
        try:
            # we use urllib instead of playwright, because we only want a simple request
            #  not a full page with all assets
            assert urllib.request.urlopen(server).getcode() == 200  # type: ignore # noqa
            break
        # todo (robbert) find out what exception to catch
        except URLError:  # server was not ready
            sleep(1)


@pytest.fixture(scope="module")
def server() -> Generator[Any, Any, Any]:
    # todo (robbert) use a better way to get the test database in the app configuration
    os.environ["APP_DATABASE_FILE"] = "database.sqlite3.test"
    process = Process(target=run_server)
    process.start()
    server_address = (
        TestSettings.HTTP_SERVER_SCHEME + TestSettings.HTTP_SERVER_HOST + ":" + str(TestSettings.HTTP_SERVER_PORT)
    )
    yield server_address
    process.terminate()
    del os.environ["APP_DATABASE_FILE"]


@pytest.fixture(scope="session")
def get_session() -> Generator[Session, Any, Any]:
    with Session(get_engine()) as session:
        yield session


def pytest_configure() -> None:
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    # todo (robbert) creating an in memory database does not work right, tables seem to get lost?
    settings.APP_DATABASE_FILE = "database.sqlite3.test"  # set to none so we'll use an in memory database


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app, raise_server_exceptions=True) as c:
        c.timeout = 5
        yield c


@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as p:
        yield p


@pytest.fixture(params=["chromium", "firefox", "webkit"])
def browser(playwright: Playwright, request: SubRequest, server: Generator[Any, Any, Any]) -> Generator[Page, Any, Any]:
    browser = getattr(playwright, request.param).launch(headless=True)
    context = browser.new_context(base_url=server)
    page = context.new_page()
    wait_for_server_ready(server)
    yield page
    browser.close()


@pytest.fixture()
def db():
    return DatabaseTestUtils()
