from fastapi.testclient import TestClient


def test_static_css(client: TestClient) -> None:
    response = client.get("/static/css/layout.css")
    assert response.status_code == 200


def test_static_js(client: TestClient) -> None:
    response = client.get("/static/js/amt.js")
    assert response.status_code == 200
