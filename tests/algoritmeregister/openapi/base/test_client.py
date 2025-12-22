import json
from unittest.mock import MagicMock

import pytest
from amt.algoritmeregister.openapi.base.client import UserApi
from amt.algoritmeregister.openapi.base.models import Flow, OrgType, User
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

    mock_api_client = MagicMock()
    mock_api_client.call_api.return_value = mock_response
    mock_api_client.select_header_accept.return_value = "application/json"
    mock_api_client.param_serialize.return_value = ("GET", "/aanleverapi/user/me", {}, None, [])

    user_api = UserApi(mock_api_client)

    # when / then
    with pytest.raises(ValueError, match="No data returned from API"):
        user_api.get_me()
