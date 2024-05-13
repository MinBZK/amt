from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from tad.main import app

# needed to make sure create_all knows about the models
from tad.models import *  # noqa: F403


@pytest.fixture(scope="module")
def client(db: Session) -> Generator[TestClient, None, None]:
    with TestClient(app, raise_server_exceptions=True) as c:
        c.timeout = 5
        yield c


@pytest.fixture(scope="module")
def db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://", poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)
