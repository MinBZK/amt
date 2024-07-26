from amt.repositories.deps import get_session
from sqlmodel import Session


def test_get_session():
    session_generator = get_session()

    session = next(session_generator)

    assert isinstance(session, Session)
