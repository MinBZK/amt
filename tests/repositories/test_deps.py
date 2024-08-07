from amt.repositories.deps import get_session
from sqlalchemy.orm import Session


def test_get_session():
    session_generator = get_session()

    session = next(session_generator)

    assert isinstance(session, Session)
