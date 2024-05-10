from fastapi.testclient import TestClient


def test_get_root(client: TestClient) -> None:
    response = client.get(
        "/",
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
