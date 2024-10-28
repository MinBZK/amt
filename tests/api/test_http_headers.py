import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_sts_header(client: AsyncClient) -> None:
    response = await client.get(
        "/",
    )
    assert response.status_code == 200
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
