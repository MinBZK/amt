from pathlib import Path

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_static_css(client: AsyncClient) -> None:
    files = Path("amt/site/static/dist").glob("*.js")
    for filename in files:
        response = await client.get(f"/static/dist/{filename.name}")
        assert response.status_code == 200
