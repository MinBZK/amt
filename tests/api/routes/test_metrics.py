import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_200(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_format(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    assert "text/plain" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_metrics_contains_db_pool_gauges(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    body = response.text
    assert "db_pool_checked_in" in body
    assert "db_pool_checked_out" in body
    assert "db_pool_overflow" in body
