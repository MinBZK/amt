import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_root(client: AsyncClient) -> None:
    response = await client.get(
        "/",
        follow_redirects=False,
    )
    # todo (robbert) this is a quick test to see if we (most likely) get the expected page
    assert response.status_code == 200
