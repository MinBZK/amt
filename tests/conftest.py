import os
from collections.abc import Generator
from multiprocessing import Process
from time import sleep

import pytest
import uvicorn
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from sqlmodel import Session
from tad.core.config import settings
from tad.core.db import get_engine
from tad.main import app


class TestSettings:
    HTTP_SERVER_SCHEME: str = "http://"
    HTTP_SERVER_HOST: str = "127.0.0.1"
    HTTP_SERVER_PORT: int = 8000


def run_server():
    uvicorn.run(app, host=TestSettings.HTTP_SERVER_HOST, port=TestSettings.HTTP_SERVER_PORT)


def wait_for_server_ready(url: str, timeout: int = 30):
    # todo we can not use playwright because it gives async errors, so we need another
    #  wait to check the server for being up
    sleep(5)


@pytest.fixture(scope="module")
def server():
    # todo (robbert) use a better way to get the test database in the app configuration
    os.environ["APP_DATABASE_FILE"] = "database.sqlite3.test"
    process = Process(target=run_server)
    process.start()
    server_address = (
        TestSettings.HTTP_SERVER_SCHEME + TestSettings.HTTP_SERVER_HOST + ":" + str(TestSettings.HTTP_SERVER_PORT)
    )
    wait_for_server_ready(server_address)
    yield server_address
    process.terminate()
    del os.environ["APP_DATABASE_FILE"]


@pytest.fixture(scope="session")
def get_session() -> Session:
    with Session(get_engine()) as session:
        yield session


def pytest_configure():
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
def browser(playwright, request):
    browser = getattr(playwright, request.param).launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    yield page
    browser.close()
