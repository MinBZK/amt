from typing import Any

import httpx
from fastapi import status

from amt.core.config import get_settings
from amt.core.exceptions import AMTHTTPException


class AlgoritmeregisterAuthError(AMTHTTPException):
    def __init__(self, detail: str = "Authentication with Algoritmeregister failed") -> None:
        self.detail: str = detail
        super().__init__(status.HTTP_401_UNAUTHORIZED, self.detail)


async def get_access_token(username: str, password: str) -> str:
    """
    Retrieve an OAuth2 access token for the Algoritmeregister API.

    Uses the OAuth2 Resource Owner Password Credentials (ROPC) flow to obtain
    an access token from the Keycloak token endpoint using user credentials.

    Args:
        username: Algoritmeregister username (email address)
        password: Algoritmeregister password

    Returns:
        The access token string

    Raises:
        AlgoritmeregisterAuthError: If token retrieval fails or credentials are not configured
    """
    settings = get_settings()

    if not settings.ALGORITMEREGISTER_TOKEN_URL:
        raise AlgoritmeregisterAuthError("ALGORITMEREGISTER_TOKEN_URL is not configured")

    if not username:
        raise AlgoritmeregisterAuthError("username must be provided")

    if not password:
        raise AlgoritmeregisterAuthError("password must be provided")

    token_data = {
        "grant_type": "password",
        "client_id": settings.ALGORITMEREGISTER_CLIENT_ID,
        "username": username,
        "password": password,
        "totp": "",
    }

    try:
        async with httpx.AsyncClient(verify=settings.VERIFY_SSL) as client:
            response = await client.post(
                settings.ALGORITMEREGISTER_TOKEN_URL,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            response.raise_for_status()

            token_response: dict[str, Any] = response.json()

            if "access_token" not in token_response:
                raise AlgoritmeregisterAuthError("No access_token in response from token endpoint")  # noqa: TRY301

            return str(token_response["access_token"])

    except httpx.HTTPStatusError as e:
        raise AlgoritmeregisterAuthError(f"Failed to retrieve access token: HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise AlgoritmeregisterAuthError(f"Failed to connect to token endpoint: {e}") from e
    except Exception as e:
        raise AlgoritmeregisterAuthError(f"Unexpected error retrieving access token: {e}") from e
