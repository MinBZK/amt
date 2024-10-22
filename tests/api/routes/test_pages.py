import pytest
from httpx import AsyncClient

from tests.database_test_utils import DatabaseTestUtils


@pytest.mark.asyncio
async def test_get_main_page(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # when
    response = await client.get("/pages/")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"<!doctype html>" in response.content.lower()
