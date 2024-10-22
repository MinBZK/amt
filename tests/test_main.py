import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_non_exisiting(client: AsyncClient) -> None:
    response = await client.get(
        "/pathdoesnotexist/",
    )
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
