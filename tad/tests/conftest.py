import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from tad.main import app

# todo(berry): add database fixtures


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app, raise_server_exceptions=True) as c:
        c.timeout = 3
        yield c


@pytest.fixture(autouse=True)
def setup_basic_environmental_variables() -> Generator[None, None, None]:  # noqa: PT004
    original_environ = dict(os.environ)
    os.environ["APP_DATABASE_PASSWORD"] = "changethis"  # noqa: S105
    yield
    os.environ.clear()
    os.environ.update(original_environ)
