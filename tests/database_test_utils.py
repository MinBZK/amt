import logging
from pathlib import Path

from pydantic import BaseModel
from sqlmodel import Session, SQLModel, select

logger = logging.getLogger(__name__)


class DatabaseTestUtils:
    def __init__(self, session: Session, database_file: Path | None = None) -> None:
        self.session: Session = session
        self.database_file: Path | None = database_file
        self.models: list[BaseModel] = []

    def given(self, models: list[BaseModel]) -> None:
        session = self.get_session()
        self.models.extend(models)
        session.add_all(models)

        session.commit()

        for model in models:
            session.refresh(model)  # inefficient, but needed to create correlations between models

    def get_session(self) -> Session:
        return self.session

    def get_database_file(self) -> Path | None:
        return self.database_file

    def exists(self, model: type[SQLModel], model_field: str, field_value: str | int) -> SQLModel | None:
        return self.get_session().exec(select(model).where(model_field == field_value)).one() is not None  # type: ignore
