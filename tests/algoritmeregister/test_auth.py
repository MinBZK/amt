import pytest
from amt.algoritmeregister.auth import AlgoritmeregisterAuthError, get_access_token
from amt.core.config import Settings
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_get_access_token_success(mocker: MockerFixture) -> None:
    # given
    mock_settings = Settings(
        ALGORITMEREGISTER_TOKEN_URL="https://keycloak.example.com/token",  # noqa: S106
    )
    mocker.patch("amt.algoritmeregister.auth.get_settings", return_value=mock_settings)

    mock_response = mocker.Mock()
    mock_response.json.return_value = {"access_token": "test_token_123"}
    mock_response.raise_for_status = mocker.Mock()

    mock_client = mocker.MagicMock()
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=None)
    mock_client.post = mocker.AsyncMock(return_value=mock_response)

    mocker.patch("amt.algoritmeregister.auth.httpx.AsyncClient", return_value=mock_client)

    # when
    token = await get_access_token("test_user@example.com", "test_password")

    # then
    assert token == "test_token_123"  # noqa: S105
    mock_client.post.assert_called_once_with(
        "https://keycloak.example.com/token",
        data={
            "grant_type": "password",
            "client_id": "authentication-client",
            "username": "test_user@example.com",
            "password": "test_password",
            "totp": "",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )


@pytest.mark.asyncio
async def test_get_access_token_missing_token_url(mocker: MockerFixture) -> None:
    # given
    mock_settings = mocker.Mock()
    mock_settings.ALGORITMEREGISTER_TOKEN_URL = None
    mocker.patch("amt.algoritmeregister.auth.get_settings", return_value=mock_settings)

    # when / then
    with pytest.raises(
        AlgoritmeregisterAuthError,
        match="ALGORITMEREGISTER_TOKEN_URL is not configured",
    ):
        await get_access_token("test_user@example.com", "test_password")


@pytest.mark.asyncio
async def test_get_access_token_missing_username(mocker: MockerFixture) -> None:
    # given
    mock_settings = Settings(
        ALGORITMEREGISTER_TOKEN_URL="https://keycloak.example.com/token",  # noqa: S106
    )
    mocker.patch("amt.algoritmeregister.auth.get_settings", return_value=mock_settings)

    # when / then
    with pytest.raises(AlgoritmeregisterAuthError, match="username must be provided"):
        await get_access_token("", "test_password")


@pytest.mark.asyncio
async def test_get_access_token_missing_password(mocker: MockerFixture) -> None:
    # given
    mock_settings = Settings(
        ALGORITMEREGISTER_TOKEN_URL="https://keycloak.example.com/token",  # noqa: S106
    )
    mocker.patch("amt.algoritmeregister.auth.get_settings", return_value=mock_settings)

    # when / then
    with pytest.raises(AlgoritmeregisterAuthError, match="password must be provided"):
        await get_access_token("test_user@example.com", "")


@pytest.mark.asyncio
async def test_get_access_token_no_access_token_in_response(
    mocker: MockerFixture,
) -> None:
    # given
    mock_settings = Settings(
        ALGORITMEREGISTER_TOKEN_URL="https://keycloak.example.com/token",  # noqa: S106
    )
    mocker.patch("amt.algoritmeregister.auth.get_settings", return_value=mock_settings)

    mock_response = mocker.Mock()
    mock_response.json.return_value = {"error": "invalid_grant"}
    mock_response.raise_for_status = mocker.Mock()

    mock_client = mocker.MagicMock()
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=None)
    mock_client.post = mocker.AsyncMock(return_value=mock_response)

    mocker.patch("amt.algoritmeregister.auth.httpx.AsyncClient", return_value=mock_client)

    # when / then
    with pytest.raises(
        AlgoritmeregisterAuthError,
        match="No access_token in response from token endpoint",
    ):
        await get_access_token("test_user@example.com", "test_password")


@pytest.mark.asyncio
async def test_get_access_token_http_error(mocker: MockerFixture) -> None:
    # given
    import httpx

    mock_settings = Settings(
        ALGORITMEREGISTER_TOKEN_URL="https://keycloak.example.com/token",  # noqa: S106
    )
    mocker.patch("amt.algoritmeregister.auth.get_settings", return_value=mock_settings)

    mock_response = mocker.Mock()
    mock_response.status_code = 401

    async def raise_http_error(*args: object, **kwargs: object) -> None:
        raise httpx.HTTPStatusError("Unauthorized", request=mocker.Mock(), response=mock_response)

    mock_client = mocker.MagicMock()
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=None)
    mock_client.post = raise_http_error

    mocker.patch("amt.algoritmeregister.auth.httpx.AsyncClient", return_value=mock_client)

    # when / then
    with pytest.raises(AlgoritmeregisterAuthError, match="Failed to retrieve access token: HTTP 401"):
        await get_access_token("test_user@example.com", "test_password")
