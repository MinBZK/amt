import logging
from pathlib import Path
from typing import TypeVar

from amt.models.base import Base
from amt.repositories.deps import AsyncSessionWithCommitFlag
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from tests.constants import default_authorizations

logger = logging.getLogger(__name__)


class DatabaseTestUtils:
    def __init__(self, session: AsyncSessionWithCommitFlag, database_file: Path | None = None) -> None:
        self.session = session
        self.database_file: Path | None = database_file
        logger.info("Using database file: %s", self.database_file)

    async def init_authorizations_and_roles(self):
        await self.given_sql(get_auth_setup_sql())
        await self.given([*default_authorizations()])

    async def given(self, models: list[Base]) -> None:
        session = self.get_session()
        # we add each model separately, because they may have relationships,
        #  that doesn't work with session.add_all
        for model in models:
            session.add(model)
            await session.commit()

        for model in models:
            await session.refresh(model)  # inefficient, but needed to create correlations between models

    async def given_sql(self, sql_statements: list[str]) -> None:
        session = self.get_session()
        for statement in sql_statements:
            await session.execute(text(statement))
        await session.commit()

    async def close(self) -> None:
        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
        await self.session.close()
        thread = (await self.session.connection()).sync_connection.connection.driver_connection  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType, reportOptionalMemberAccess, reportAttributeAccessIssue]
        logger.info(
            f"Closing session {thread} / {self.session.info.get('id', 'unknown')} /"
            f"{self.session} and database file {self.database_file}"
        )

    def get_session(self) -> AsyncSessionWithCommitFlag:
        return self.session

    def get_database_file(self) -> Path | None:
        return self.database_file

    async def exists(self, model: type[Base], model_field: str, field_value: str | int) -> bool:
        try:
            result = await self.get_session().execute(select(model).where(getattr(model, model_field) == field_value))
            return result.scalar_one_or_none() is not None
        except AttributeError as err:
            raise ValueError(f"Field '{model_field}' does not exist in model {model.__name__}") from err

    BaseType = TypeVar("BaseType", bound=Base)

    async def get(self, model: type[BaseType], model_field: str, field_value: str | int) -> list[BaseType]:
        try:
            query = select(model).where(getattr(model, model_field) == field_value)
            result = await self.get_session().execute(query)
            return list(result.scalars().all())
        except AttributeError as err:
            raise ValueError(f"Field '{model_field}' does not exist in model {model.__name__}") from err


def get_auth_setup_sql():
    file_path = "tests/auth_setup.sql"
    with open(file_path) as f:
        sql_content = f.read()
    sql_statements = [stmt.strip() + ";" for stmt in sql_content.split(";") if stmt.strip()]
    return sql_statements
