from sqlmodel import create_engine

from tad.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)
