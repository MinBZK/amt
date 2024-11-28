import logging
from pathlib import Path

from amt.models.base import Base
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DatabaseTestUtils:
    def __init__(self, session: AsyncSession, database_file: Path | None = None) -> None:
        self.session: AsyncSession = session
        self.database_file: Path | None = database_file

    async def given(self, models: list[Base]) -> None:
        session = self.get_session()
        # we add each model separately, because they may have relationships,
        #  that doesn't work with session.add_all
        for model in models:
            session.add(model)
            await session.commit()

        for model in models:
            await session.refresh(model)  # inefficient, but needed to create correlations between models

    def get_session(self) -> AsyncSession:
        return self.session

    def get_database_file(self) -> Path | None:
        return self.database_file

    async def exists(self, model: type[Base], model_field: str, field_value: str | int) -> bool:
        try:
            result = await self.get_session().execute(select(model).where(getattr(model, model_field) == field_value))
            return result.scalar_one_or_none() is not None
        except AttributeError as err:
            raise ValueError(f"Field '{model_field}' does not exist in model {model.__name__}") from err

    async def get(self, model: type[Base], model_field: str, field_value: str | int) -> list[Base]:
        try:
            query = select(model).where(getattr(model, model_field) == field_value)
            result = await self.get_session().execute(query)
            return list(result.scalars().all())
        except AttributeError as err:
            raise ValueError(f"Field '{model_field}' does not exist in model {model.__name__}") from err
