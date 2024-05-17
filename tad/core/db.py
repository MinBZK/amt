from sqlalchemy.engine.base import Engine
from sqlmodel import Session, create_engine, select

from tad.core.config import settings

engine: Engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)


async def check_db():
    with Session(engine) as session:
        session.exec(select(1))
