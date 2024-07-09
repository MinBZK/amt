from collections.abc import Generator

from sqlmodel import Session

from amt.core.db import get_engine


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
