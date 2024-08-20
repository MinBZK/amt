from fastapi.testclient import TestClient


def test_static_css(client: TestClient) -> None:
    response = client.get("/static/css/2cols.css")
    assert response.status_code == 200
