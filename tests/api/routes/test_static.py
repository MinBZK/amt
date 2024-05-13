import pytest
from fastapi.testclient import TestClient


@pytest.mark.skip(reason="Not working yet")
def test_static_css(client: TestClient) -> None:
    response = client.get("/static/styles.css")
    assert response.status_code == 200


@pytest.mark.skip(reason="Not working yet")
def test_static_js(client: TestClient) -> None:
    response = client.get("/static/main.js")
    assert response.status_code == 200
