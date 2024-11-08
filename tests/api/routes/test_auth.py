import pytest
from httpx import AsyncClient
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_auth_profile(client: AsyncClient, mocker: MockerFixture) -> None:
    mocker.patch("amt.api.routes.auth.get_user", return_value="test_user_for_auth_profile")
    response = await client.get("/auth/profile")

    assert b"https://gravatar.com/" in response.content
