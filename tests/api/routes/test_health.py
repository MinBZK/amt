from fastapi.testclient import TestClient
from tad.core.config import VERSION


def test_health_ready(client: TestClient) -> None:
    response = client.get(
        "/health/ready",
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"status": "ok", "version": VERSION}


def test_health_live(client: TestClient) -> None:
    response = client.get(
        "/health/live",
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"status": "ok", "version": VERSION}
