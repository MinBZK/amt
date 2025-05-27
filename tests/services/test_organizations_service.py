import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from amt.core.exceptions import AMTAuthorizationError, AMTNotFound
from amt.services.organizations import OrganizationsService
from tests.constants import default_organization, default_user


@pytest.mark.asyncio
async def test_save() -> None:
    # Given
    organizations_repository = AsyncMock()
    organizations_repository.save.return_value = default_organization()

    authorization_service = AsyncMock()
    authorization_service.get_role.return_value = MagicMock(id=1)

    users_service = AsyncMock()
    users_service.find_by_id.return_value = default_user()

    service = OrganizationsService(
        organizations_repository=organizations_repository,
        authorization_service=authorization_service,
        users_service=users_service,
    )

    # When
    result = await service.save(name="test org", slug="test-org", created_by_user_id=str(default_user().id))

    # Then
    assert result.name == "default organization"
    assert result.slug == "default-organization"

    organizations_repository.save.assert_called_once()
    users_service.find_by_id.assert_called_once_with(str(default_user().id))


@pytest.mark.asyncio
async def test_save_user_not_found() -> None:
    # Given
    organizations_repository = AsyncMock()
    authorization_service = AsyncMock()
    users_service = AsyncMock()
    users_service.find_by_id.return_value = None

    service = OrganizationsService(
        organizations_repository=organizations_repository,
        authorization_service=authorization_service,
        users_service=users_service,
    )

    # When/Then
    with pytest.raises(AMTNotFound):
        await service.save(name="test org", slug="test-org", created_by_user_id="non-existent-user")


@pytest.mark.asyncio
async def test_get_organizations_for_user() -> None:
    # Given
    expected_orgs = [default_organization(), default_organization(name="org2", slug="org2")]
    organizations_repository = AsyncMock()
    organizations_repository.find_by.return_value = expected_orgs

    authorization_service = AsyncMock()
    users_service = AsyncMock()

    service = OrganizationsService(
        organizations_repository=organizations_repository,
        authorization_service=authorization_service,
        users_service=users_service,
    )

    user_id = str(uuid.uuid4())

    # When
    result = await service.get_organizations_for_user(user_id)

    # Then
    assert result == expected_orgs
    organizations_repository.find_by.assert_called_once()
    assert organizations_repository.find_by.call_args[1]["user_id"] == uuid.UUID(user_id)


@pytest.mark.asyncio
async def test_get_organizations_for_user_none_user_id() -> None:
    # Given
    organizations_repository = AsyncMock()
    authorization_service = AsyncMock()
    users_service = AsyncMock()

    service = OrganizationsService(
        organizations_repository=organizations_repository,
        authorization_service=authorization_service,
        users_service=users_service,
    )

    # When/Then
    with pytest.raises(AMTAuthorizationError):
        await service.get_organizations_for_user(None)


@pytest.mark.asyncio
async def test_add_users() -> None:
    # Given
    organization = default_organization()
    # Mock users attribute for testing purposes
    organization.users = []  # type: ignore

    user1 = default_user()
    user2 = default_user(id="4738b1e151dc46219556a5662b26517c", name="Test User 2")

    organizations_repository = AsyncMock()
    organizations_repository.save.return_value = organization

    authorization_service = AsyncMock()

    users_service = AsyncMock()
    # Set up the side effect to return different users based on ID
    users_service.find_by_id.side_effect = lambda id_str: user1 if str(id_str) == str(user1.id) else user2  # pyright: ignore

    service = OrganizationsService(
        organizations_repository=organizations_repository,
        authorization_service=authorization_service,
        users_service=users_service,
    )

    # When
    result = await service.add_users(organization, [str(user1.id), str(user2.id)])

    # Then
    # Use type ignore for the tests as we're mocking the users attribute
    assert len(result.users) == 2  # type: ignore
    assert user1 in result.users  # type: ignore
    assert user2 in result.users  # type: ignore
    organizations_repository.save.assert_called_once_with(organization)


@pytest.mark.asyncio
async def test_find_by_slug() -> None:
    # Given
    organizations_repository = AsyncMock()
    organizations_repository.find_by_slug.return_value = default_organization()

    authorization_service = AsyncMock()
    users_service = AsyncMock()

    service = OrganizationsService(
        organizations_repository=organizations_repository,
        authorization_service=authorization_service,
        users_service=users_service,
    )

    # When
    result = await service.find_by_slug("default-organization")

    # Then
    assert result.name == "default organization"
    assert result.slug == "default-organization"
    organizations_repository.find_by_slug.assert_called_once_with("default-organization")


@pytest.mark.asyncio
async def test_get_by_id() -> None:
    # Given
    organizations_repository = AsyncMock()
    organizations_repository.find_by_id.return_value = default_organization()

    authorization_service = AsyncMock()
    users_service = AsyncMock()

    service = OrganizationsService(
        organizations_repository=organizations_repository,
        authorization_service=authorization_service,
        users_service=users_service,
    )

    # When
    result = await service.get_by_id(1)

    # Then
    assert result.name == "default organization"
    assert result.slug == "default-organization"
    organizations_repository.find_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_find_by_id_and_user_id() -> None:
    # Given
    organizations_repository = AsyncMock()
    organizations_repository.find_by_id_and_user_id.return_value = default_organization()

    authorization_service = AsyncMock()
    users_service = AsyncMock()

    service = OrganizationsService(
        organizations_repository=organizations_repository,
        authorization_service=authorization_service,
        users_service=users_service,
    )

    user_id = str(uuid.uuid4())

    # When
    result = await service.find_by_id_and_user_id(1, user_id)

    # Then
    assert result.name == "default organization"
    assert result.slug == "default-organization"
    organizations_repository.find_by_id_and_user_id.assert_called_once_with(1, user_id)


@pytest.mark.asyncio
async def test_update() -> None:
    # Given
    organization = default_organization()

    organizations_repository = AsyncMock()
    organizations_repository.save.return_value = organization

    authorization_service = AsyncMock()
    users_service = AsyncMock()

    service = OrganizationsService(
        organizations_repository=organizations_repository,
        authorization_service=authorization_service,
        users_service=users_service,
    )

    # When
    result = await service.update(organization)

    # Then
    assert result == organization
    organizations_repository.save.assert_called_once_with(organization)


@pytest.mark.asyncio
async def test_remove_user() -> None:
    # Given
    organization = default_organization()
    user = default_user()

    organizations_repository = AsyncMock()
    authorization_service = AsyncMock()
    users_service = AsyncMock()

    service = OrganizationsService(
        organizations_repository=organizations_repository,
        authorization_service=authorization_service,
        users_service=users_service,
    )

    # When
    await service.remove_user(organization, user)

    # Then
    authorization_service.remove_all_roles.assert_called_once_with(user.id, organization)
