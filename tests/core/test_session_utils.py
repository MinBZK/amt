import pytest
from amt.core.session_utils import (
    clear_algoritmeregister_credentials,
    get_algoritmeregister_credentials,
    store_algoritmeregister_credentials,
)
from amt.schema.algoritmeregister import AlgoritmeregisterCredentials
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_store_and_get_algoritmeregister_credentials(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {}  # type: ignore
    mock_request.cookies = {}  # type: ignore
    credentials = AlgoritmeregisterCredentials(username="test_user", password="test_pass", token="test_token")  # noqa: S106

    # when
    store_algoritmeregister_credentials(mock_request, credentials)
    result = get_algoritmeregister_credentials(mock_request)

    # then
    assert result == credentials
    assert mock_request.session["algoritmeregister_credentials"] == {  # type: ignore
        "username": "test_user",
        "password": "test_pass",
        "token": "test_token",
    }


@pytest.mark.asyncio
async def test_get_algoritmeregister_credentials_returns_none_when_not_set(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {}  # type: ignore
    mock_request.cookies = {}  # type: ignore

    # when
    result = get_algoritmeregister_credentials(mock_request)

    # then
    assert result is None


@pytest.mark.asyncio
async def test_clear_algoritmeregister_credentials(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {}  # type: ignore
    mock_request.cookies = {}  # type: ignore
    credentials = AlgoritmeregisterCredentials(username="test_user", password="test_pass", token="test_token")  # noqa: S106
    store_algoritmeregister_credentials(mock_request, credentials)

    # when
    clear_algoritmeregister_credentials(mock_request)
    result = get_algoritmeregister_credentials(mock_request)

    # then
    assert result is None
    assert "algoritmeregister_credentials" not in mock_request.session  # type: ignore


@pytest.mark.asyncio
async def test_clear_algoritmeregister_credentials_when_not_set(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {}  # type: ignore
    mock_request.cookies = {}  # type: ignore

    # when
    clear_algoritmeregister_credentials(mock_request)

    # then
    assert "algoritmeregister_credentials" not in mock_request.session  # type: ignore
