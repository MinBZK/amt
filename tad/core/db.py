from sqlalchemy.engine.base import Engine
from sqlmodel import Session, create_engine, select

from tad.core.config import settings

_engine: None | Engine = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    return _engine


async def check_db():
    with Session(get_engine()) as session:
        session.exec(select(1))
