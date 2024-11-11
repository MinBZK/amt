from unittest.mock import AsyncMock

import pytest
from amt.core.exceptions import AMTRepositoryError
from amt.repositories.users import UsersRepository
from sqlalchemy.exc import SQLAlchemyError
from tests.constants import default_user
from tests.database_test_utils import DatabaseTestUtils


@pytest.mark.asyncio
async def test_find_by_id(db: DatabaseTestUtils):
    await db.given([default_user()])
    users_repository = UsersRepository(db.get_session())
    result = await users_repository.find_by_id(default_user().id)
    assert result is not None
    assert result.id == default_user().id
    assert result.name == default_user().name


@pytest.mark.asyncio
async def test_upsert_new(db: DatabaseTestUtils):
    new_user = default_user()
    users_repository = UsersRepository(db.get_session())
    await users_repository.upsert(new_user)
    result = await users_repository.find_by_id(new_user.id)
    assert result is not None
    assert result.id == new_user.id
    assert result.name == new_user.name


@pytest.mark.asyncio
async def test_upsert_existing(db: DatabaseTestUtils):
    await db.given([default_user()])
    new_user = default_user(name="John Smith New")
    users_repository = UsersRepository(db.get_session())
    await users_repository.upsert(new_user)
    result = await users_repository.find_by_id(new_user.id)
    assert result is not None
    assert result.id == new_user.id
    assert result.name == new_user.name


@pytest.mark.asyncio
async def test_upsert_error(db: DatabaseTestUtils):
    new_user = default_user(name="John Smith New")
    users_repository = UsersRepository(db.get_session())
    users_repository.find_by_id = AsyncMock(side_effect=SQLAlchemyError("Database error"))
    with pytest.raises(AMTRepositoryError):
        await users_repository.upsert(new_user)
