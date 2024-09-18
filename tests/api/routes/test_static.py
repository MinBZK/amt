from pathlib import Path

from fastapi.testclient import TestClient


def test_static_css(client: TestClient) -> None:
    files = Path("amt/site/static/dist").glob("*.js")
    for filename in files:
        response = client.get(f"/static/dist/{filename.name}")
        assert response.status_code == 200
