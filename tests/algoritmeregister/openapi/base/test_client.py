import json
from unittest.mock import MagicMock

import pytest
from amt.algoritmeregister.openapi.base.client import OrganisationApi, UserApi
from amt.algoritmeregister.openapi.base.models import Flow, GetOrganisationsResponse, OrgType, User
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_get_me_success(mocker: MockerFixture) -> None:
    # given
    user_data = {
        "id": "user-123",
        "username": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "roles": ["admin"],
        "organisations": [
            {
                "id": 1,
                "name": "Test Organisation",
                "code": "gm0001",
                "org_id": "org-1",
                "type": "gemeente",
                "flow": "ictu_last",
                "show_page": True,
            }
        ],
    }

    mock_response = MagicMock()
    mock_response.data = json.dumps(user_data).encode()
    mock_response.status = 200

    mock_api_client = MagicMock()
    mock_api_client.call_api.return_value = mock_response
    mock_api_client.select_header_accept.return_value = "application/json"
    mock_api_client.param_serialize.return_value = ("GET", "/aanleverapi/user/me", {}, None, [])

    user_api = UserApi(mock_api_client)

    # when
    result = user_api.get_me()

    # then
    assert isinstance(result, User)
    assert result.id == "user-123"
    assert result.username == "test@example.com"
    assert result.first_name == "Test"
    assert result.last_name == "User"
    assert len(result.organisations) == 1
    assert result.organisations[0].name == "Test Organisation"
    assert result.organisations[0].code == "gm0001"
    assert result.organisations[0].type == OrgType.GEMEENTE
    assert result.organisations[0].flow == Flow.ICTU_LAST


@pytest.mark.asyncio
async def test_get_me_multiple_organisations(mocker: MockerFixture) -> None:
    # given
    user_data = {
        "id": "user-456",
        "username": "multi@example.com",
        "first_name": "Multi",
        "last_name": "Org",
        "roles": ["admin", "orgdetail"],
        "organisations": [
            {
                "id": 1,
                "name": "Municipality One",
                "code": "gm0001",
                "org_id": "org-1",
                "type": "gemeente",
                "flow": "ictu_last",
                "show_page": True,
            },
            {
                "id": 2,
                "name": "Province Two",
                "code": "pv0002",
                "org_id": "org-2",
                "type": "provincie",
                "flow": "self_publish_two",
                "show_page": False,
            },
        ],
    }

    mock_response = MagicMock()
    mock_response.data = json.dumps(user_data).encode()
    mock_response.status = 200

    mock_api_client = MagicMock()
    mock_api_client.call_api.return_value = mock_response
    mock_api_client.select_header_accept.return_value = "application/json"
    mock_api_client.param_serialize.return_value = ("GET", "/aanleverapi/user/me", {}, None, [])

    user_api = UserApi(mock_api_client)

    # when
    result = user_api.get_me()

    # then
    assert len(result.organisations) == 2
    assert result.organisations[0].type == OrgType.GEMEENTE
    assert result.organisations[1].type == OrgType.PROVINCIE
    assert result.organisations[1].flow == Flow.SELF_PUBLISH_TWO


@pytest.mark.asyncio
async def test_get_me_no_data_raises_error(mocker: MockerFixture) -> None:
    # given
    mock_response = MagicMock()
    mock_response.data = None
    mock_response.status = 200

    mock_api_client = MagicMock()
    mock_api_client.call_api.return_value = mock_response
    mock_api_client.select_header_accept.return_value = "application/json"
    mock_api_client.param_serialize.return_value = ("GET", "/aanleverapi/user/me", {}, None, [])

    user_api = UserApi(mock_api_client)

    # when / then
    with pytest.raises(ValueError, match="No data returned from API"):
        user_api.get_me()


@pytest.mark.asyncio
async def test_get_all_organisations_success(mocker: MockerFixture) -> None:
    # given
    response_data = {
        "organisations": [
            {
                "id": 1,
                "name": "Test Organisation",
                "code": "gm0001",
                "org_id": "org-1",
                "type": "gemeente",
                "flow": "ictu_last",
                "show_page": True,
            },
            {
                "id": 2,
                "name": "Another Organisation",
                "code": "pv0001",
                "org_id": "org-2",
                "type": "provincie",
                "flow": "self_publish_two",
                "show_page": False,
            },
        ],
        "count": 2,
    }

    mock_response = MagicMock()
    mock_response.data = json.dumps(response_data).encode()
    mock_response.status = 200

    mock_api_client = MagicMock()
    mock_api_client.call_api.return_value = mock_response
    mock_api_client.param_serialize.return_value = ("GET", "/aanleverapi/organisation", {}, None, [])

    organisation_api = OrganisationApi(mock_api_client)

    # when
    result = organisation_api.get_all()

    # then
    assert isinstance(result, GetOrganisationsResponse)
    assert result.count == 2
    assert len(result.organisations) == 2
    assert result.organisations[0].name == "Test Organisation"
    assert result.organisations[0].type == OrgType.GEMEENTE
    assert result.organisations[1].type == OrgType.PROVINCIE
    assert result.organisations[1].flow == Flow.SELF_PUBLISH_TWO


@pytest.mark.asyncio
async def test_get_all_organisations_with_query_params(mocker: MockerFixture) -> None:
    # given
    response_data: dict[str, list[dict[str, object]] | int] = {"organisations": [], "count": 0}

    mock_response = MagicMock()
    mock_response.data = json.dumps(response_data).encode()
    mock_response.status = 200

    mock_api_client = MagicMock()
    mock_api_client.call_api.return_value = mock_response
    mock_api_client.param_serialize.return_value = ("GET", "/aanleverapi/organisation", {}, None, [])

    organisation_api = OrganisationApi(mock_api_client)

    # when
    result = organisation_api.get_all(limit=100, skip=10, q="test")

    # then
    mock_api_client.param_serialize.assert_called_once()
    call_kwargs = mock_api_client.param_serialize.call_args
    assert call_kwargs.kwargs["query_params"] == [("limit", "100"), ("skip", "10"), ("q", "test")]
    assert result.count == 0


@pytest.mark.asyncio
async def test_get_all_organisations_api_error(mocker: MockerFixture) -> None:
    # given
    mock_response = MagicMock()
    mock_response.data = b"Unauthorized"
    mock_response.status = 401

    mock_api_client = MagicMock()
    mock_api_client.call_api.return_value = mock_response
    mock_api_client.param_serialize.return_value = ("GET", "/aanleverapi/organisation", {}, None, [])

    organisation_api = OrganisationApi(mock_api_client)

    # when / then
    with pytest.raises(ValueError, match="API request failed with status 401"):
        organisation_api.get_all()
