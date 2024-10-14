import logging
from pathlib import Path

from amt.models.base import Base
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DatabaseTestUtils:
    def __init__(self, session: Session, database_file: Path | None = None) -> None:
        self.session: Session = session
        self.database_file: Path | None = database_file

    def given(self, models: list[Base]) -> None:
        session = self.get_session()
        session.add_all(models)

        session.commit()

        for model in models:
            session.refresh(model)  # inefficient, but needed to create correlations between models

    def get_session(self) -> Session:
        return self.session

    def get_database_file(self) -> Path | None:
        return self.database_file

    def exists(self, model: type[Base], model_field: str, field_value: str | int) -> Base | None:
        return self.get_session().execute(select(model).where(model_field == field_value)).one() is not None  # type: ignore

    def get(self, model: type[Base], model_field: str, field_value: str | int) -> list[Base]:
        try:
            query = select(model).where(getattr(model, model_field) == field_value)
            result = self.get_session().execute(query)
            return list(result.scalars().all())
        except AttributeError as err:
            raise ValueError(f"Field '{model_field}' does not exist in model {model.__name__}") from err
