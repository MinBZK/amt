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


def run_server():
    settings.APP_DATABASE_FILE = "database.sqlite3.test"
    uvicorn.run(app, host="127.0.0.1", port=8000)


def wait_for_server_ready(url: str, timeout: int = 30):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for _ in range(timeout):
            try:
                page.goto(url)
                browser.close()
                return True  # noqa
            # todo (robbert) find out what exception to catch
            except Exception:
                sleep(1)
        browser.close()
        raise Exception(f"Server at {url} did not become ready within {timeout} seconds")  # noqa: TRY003 TRY002


@pytest.fixture(scope="module")
def _start_server():
    process = Process(target=run_server)
    process.start()
    wait_for_server_ready("http://127.0.0.1:8000")
    yield
    process.terminate()


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
