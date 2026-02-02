"""
Client for the Algoritmeregister Base API.

This module provides a client for base API endpoints that are not part of the versioned API.
These endpoints are on /aanleverapi (without version suffix).
"""

from amt.algoritmeregister.openapi.base.models import GetOrganisationsResponse, User
from amt.algoritmeregister.openapi.v1_0.client.openapi_client import ApiClient


class UserApi:
    """
    Client for the User API endpoints.

    Note: These endpoints are on /aanleverapi (base path), not /aanleverapi/v1_0.
    Configure the ApiClient with the base URL (without v1_0) when using this class.
    """

    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client

    def get_me(self) -> User:
        """Get the current authenticated user including their organisations and roles."""
        _param = self.api_client.param_serialize(  # type: ignore[reportUnknownMemberType]
            method="GET",
            resource_path="/user/me",
            auth_settings=["OAuth2AuthorizationCodeBearer"],
        )

        response = self.api_client.call_api(*_param)  # type: ignore[reportUnknownMemberType]
        response.read()

        status: int = response.status  # type: ignore[reportUnknownMemberType]
        if status >= 400:
            data_str = response.data.decode() if response.data else "No response body"  # type: ignore[reportUnknownMemberType]
            raise ValueError(f"API request failed with status {status}: {data_str}")

        data: bytes | None = response.data  # type: ignore[reportUnknownMemberType]
        if data is None:
            raise ValueError("No data returned from API")  # pragma: no cover

        return User.model_validate_json(data)  # type: ignore[reportUnknownArgumentType]


class OrganisationApi:
    """
    Client for the Organisation API endpoints.

    Note: These endpoints are on /aanleverapi (base path), not /aanleverapi/v1_0.
    Configure the ApiClient with the base URL (without v1_0) when using this class.
    """

    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client

    def get_all(self, limit: int = 10000, skip: int = 0, q: str | None = None) -> GetOrganisationsResponse:
        """Get all organisations with pagination."""
        query_params: list[tuple[str, str]] = [("limit", str(limit)), ("skip", str(skip))]
        if q is not None:
            query_params.append(("q", q))

        _param = self.api_client.param_serialize(  # type: ignore[reportUnknownMemberType]
            method="GET",
            resource_path="/organisation",
            query_params=query_params,
            auth_settings=["OAuth2AuthorizationCodeBearer"],
        )

        response = self.api_client.call_api(*_param)  # type: ignore[reportUnknownMemberType]
        response.read()

        status: int = response.status  # type: ignore[reportUnknownMemberType]
        if status >= 400:
            data_str = response.data.decode() if response.data else "No response body"  # type: ignore[reportUnknownMemberType]
            raise ValueError(f"API request failed with status {status}: {data_str}")

        data: bytes | None = response.data  # type: ignore[reportUnknownMemberType]
        if data is None:
            raise ValueError("No data returned from API")  # pragma: no cover

        return GetOrganisationsResponse.model_validate_json(data)  # type: ignore[reportUnknownArgumentType]
