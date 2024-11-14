import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.enable_auth
async def test_auth_not_algorithm(client: AsyncClient) -> None:
    response = await client.get("/algorithms/", follow_redirects=True)

    assert response.status_code == 200
    assert response.url == "http://testserver/"
