from uuid import UUID

import pytest
from amt.repositories.users import UsersRepository
from amt.services.users import UsersService
from pytest_mock import MockFixture
from tests.constants import default_user


@pytest.mark.asyncio
async def test_get_user(mocker: MockFixture):
    # Given
    id = UUID("3d284d80-fc47-41ab-9696-fab562bacbd5")
    name = "John Smith"
    users_service = UsersService(
        repository=mocker.AsyncMock(spec=UsersRepository),
    )
    users_service.repository.find_by_id.return_value = default_user(id=id, name=name)  # type: ignore

    # When
    user = await users_service.get(id)

    # Then
    assert user is not None
    assert user.id == id
    assert user.name == name
    users_service.repository.find_by_id.assert_awaited_once_with(id)  # type: ignore


@pytest.mark.asyncio
async def test_create_or_update(mocker: MockFixture):
    # Given
    user = default_user()
    users_service = UsersService(
        repository=mocker.AsyncMock(spec=UsersRepository),
    )
    users_service.repository.upsert.return_value = user  # type: ignore

    # When
    retreived_user = await users_service.create_or_update(user)

    # Then
    assert retreived_user is not None
    assert retreived_user.id == user.id
    assert retreived_user.name == user.name
    users_service.repository.upsert.assert_awaited_once_with(user)  # type: ignore
