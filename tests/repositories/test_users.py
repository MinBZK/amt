from unittest.mock import AsyncMock
from uuid import uuid4

# pyright: reportDeprecated=false
import pytest
from amt.core.exceptions import AMTRepositoryError
from amt.repositories.users import UsersRepository
from sqlalchemy.exc import SQLAlchemyError
from tests.constants import default_organization, default_user
from tests.database_test_utils import DatabaseTestUtils


@pytest.mark.asyncio
async def test_find_by_id(db: DatabaseTestUtils):
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()
    users_repository = UsersRepository(db.get_session())
    result = await users_repository.find_by_id(default_user().id)
    assert result is not None
    assert result.id == default_user().id
    assert result.name == default_user().name


@pytest.mark.asyncio
async def test_find_by_id_string_id(db: DatabaseTestUtils):
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()
    users_repository = UsersRepository(db.get_session())
    result = await users_repository.find_by_id(str(default_user().id))
    assert result is not None
    assert result.id == default_user().id
    assert result.name == default_user().name


@pytest.mark.asyncio
async def test_find_by_id_not_found(db: DatabaseTestUtils):
    # given
    users_repository = UsersRepository(db.get_session())

    # when
    result = await users_repository.find_by_id(uuid4())

    # then
    assert result is None


@pytest.mark.asyncio
async def test_find_by_id_cached(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()
    users_repository = UsersRepository(db.get_session())

    # when - first call to populate cache
    result1 = await users_repository.find_by_id(default_user().id)

    # then - second call should use cache
    result2 = await users_repository.find_by_id(default_user().id)

    assert result1 is not None
    assert result2 is not None
    assert result1.id == result2.id
    assert id(result1) == id(result2)  # Same object reference if cached


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
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()
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


@pytest.mark.asyncio
async def test_find_all_basic(db: DatabaseTestUtils):
    # given
    user1 = default_user(name="Alice Smith")
    user2 = default_user(id=uuid4(), name="Bob Jones")
    await db.given([user1, user2, default_organization()])
    await db.init_authorizations_and_roles()
    users_repository = UsersRepository(db.get_session())

    # when - using deprecated method intentionally for testing
    results = await users_repository.find_all()

    # then
    assert len(results) == 2
    names = [user.name for user in results]
    assert "Alice Smith" in names
    assert "Bob Jones" in names


@pytest.mark.asyncio
async def test_find_all_with_search(db: DatabaseTestUtils):
    # given
    user1 = default_user(name="Alice Smith")
    user2 = default_user(id=uuid4(), name="Bob Jones")
    await db.given([user1, user2, default_organization()])
    await db.init_authorizations_and_roles()
    users_repository = UsersRepository(db.get_session())

    # when - using deprecated method intentionally for testing
    results = await users_repository.find_all(search="Alice")

    # then
    assert len(results) == 1
    assert results[0].name == "Alice Smith"


@pytest.mark.asyncio
async def test_find_all_with_sort_ascending(db: DatabaseTestUtils):
    # given
    user1 = default_user(name="Zack Smith")
    user2 = default_user(id=uuid4(), name="Adam Jones")
    await db.given([user1, user2, default_organization()])
    await db.init_authorizations_and_roles()
    users_repository = UsersRepository(db.get_session())

    # when - using deprecated method intentionally for testing
    results = await users_repository.find_all(sort={"name": "ascending"})

    # then
    assert len(results) == 2
    assert results[0].name == "Adam Jones"
    assert results[1].name == "Zack Smith"


@pytest.mark.asyncio
async def test_find_all_with_sort_descending(db: DatabaseTestUtils):
    # given
    user1 = default_user(name="Adam Smith")
    user2 = default_user(id=uuid4(), name="Zack Jones")
    await db.given([user1, user2, default_organization()])
    await db.init_authorizations_and_roles()
    users_repository = UsersRepository(db.get_session())

    # when - using deprecated method intentionally for testing
    results = await users_repository.find_all(sort={"name": "descending"})

    # then
    assert len(results) == 2
    assert results[0].name == "Zack Jones"
    assert results[1].name == "Adam Smith"


@pytest.mark.asyncio
async def test_find_all_with_skip_and_limit(db: DatabaseTestUtils):
    # given
    user1 = default_user(name="A User")
    user2 = default_user(id=uuid4(), name="B User")
    user3 = default_user(id=uuid4(), name="C User")
    await db.given([user1, user2, user3, default_organization()])
    await db.init_authorizations_and_roles()
    users_repository = UsersRepository(db.get_session())

    # when - using deprecated method intentionally for testing
    results = await users_repository.find_all(sort={"name": "ascending"}, skip=1, limit=1)

    # then
    assert len(results) == 1
    assert results[0].name == "B User"
