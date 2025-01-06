import pytest
from amt.core.authorization import AuthorizationResource, AuthorizationType, AuthorizationVerb
from amt.repositories.authorizations import AuthorizationRepository
from amt.services.authorization import AuthorizationService
from pytest_mock import MockFixture
from tests.constants import default_auth_user


@pytest.mark.asyncio
async def test_authorization_get_auth_read(mocker: MockFixture):
    # Given

    authorization_service = AuthorizationService()
    authorization_service.repository = mocker.AsyncMock(spec=AuthorizationRepository)
    authorization_service.repository.find_by_user.return_value = [
        (AuthorizationResource.ORGANIZATION_INFO, [AuthorizationVerb.READ], AuthorizationType.ORGANIZATION, 1)
    ]

    # When
    authorizations = await authorization_service.find_by_user(default_auth_user())

    # Then
    assert authorizations == {"organization/1": [AuthorizationVerb.READ]}


@pytest.mark.asyncio
async def test_authorization_get_auth_none(mocker: MockFixture):
    # Given

    authorization_service = AuthorizationService()
    authorization_service.repository = mocker.AsyncMock(spec=AuthorizationRepository)
    authorization_service.repository.find_by_user.return_value = []

    # When
    authorizations = await authorization_service.find_by_user(default_auth_user())

    # Then
    assert authorizations == {}
