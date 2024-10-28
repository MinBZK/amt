import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_ready(client: AsyncClient) -> None:
    response = await client.get(
        "/health/ready",
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_live(client: AsyncClient) -> None:
    response = await client.get(
        "/health/live",
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"status": "ok"}
