from sqlmodel import SQLModel, create_engine

from tad.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)

def init_db() -> None:
    SQLModel.metadata.create_all(engine)


