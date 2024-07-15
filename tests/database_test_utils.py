from pydantic import BaseModel
from sqlmodel import Session, SQLModel, select
from tad.core.db import get_engine


class DatabaseTestUtils:
    def __init__(self, session: Session) -> None:
        SQLModel.metadata.drop_all(get_engine())
        SQLModel.metadata.create_all(get_engine())
        self.session: Session = session
        self.models: list[BaseModel] = []

    def __del__(self):
        pass

    def given(self, models: list[BaseModel]) -> None:
        self.models.extend(models)
        self.session.add_all(models)

        self.session.commit()

        for model in models:
            self.session.refresh(model)  # inefficient, but needed to create correlations between models

    def get_session(self) -> Session:
        return self.session

    def exists(self, model: type[SQLModel], model_field: str, field_value: str | int) -> SQLModel | None:
        return self.get_session().exec(select(model).where(model_field == field_value)).one() is not None  # type: ignore
