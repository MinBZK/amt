import pytest
from amt.core.authorization import AuthorizationResource, AuthorizationType, AuthorizationVerb
from amt.repositories.algorithms import AlgorithmsRepository
from amt.repositories.authorizations import AuthorizationRepository
from amt.repositories.organizations import OrganizationsRepository
from amt.services.authorization import AuthorizationsService
from pytest_mock import MockFixture
from tests.constants import default_auth_user


@pytest.mark.asyncio
async def test_authorization_get_auth_read(mocker: MockFixture):
    # Given

    authorization_repository = mocker.AsyncMock(spec=AuthorizationRepository)
    authorization_repository.find_by_user.return_value = [
        (AuthorizationResource.ORGANIZATION_INFO, [AuthorizationVerb.READ], AuthorizationType.ORGANIZATION, 1)
    ]
    authorization_service = AuthorizationsService(
        repository=authorization_repository,
        algorithms_repository=mocker.AsyncMock(spec=AlgorithmsRepository),
        organizations_repository=mocker.AsyncMock(spec=OrganizationsRepository),
    )

    # When
    authorizations = await authorization_service.find_by_user(default_auth_user())

    # Then
    assert "organization/1" in authorizations
    assert authorizations["organization/1"] == [AuthorizationVerb.READ]


@pytest.mark.asyncio
async def test_authorization_get_auth_none(mocker: MockFixture):
    # Given

    authorization_repository = mocker.AsyncMock(spec=AuthorizationRepository)
    authorization_repository.find_by_user.return_value = []
    authorization_service = AuthorizationsService(
        repository=authorization_repository,
        algorithms_repository=mocker.AsyncMock(spec=AlgorithmsRepository),
        organizations_repository=mocker.AsyncMock(spec=OrganizationsRepository),
    )

    # When
    auth_user = default_auth_user()
    auth_user["sub"] = "23d4c01d-23b9-4096-acda-d9be5c66c243"
    authorizations = await authorization_service.find_by_user(auth_user)

    # Then
    assert len(authorizations) == 2
