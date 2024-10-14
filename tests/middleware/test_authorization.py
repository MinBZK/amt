import pytest
from fastapi.testclient import TestClient


@pytest.mark.enable_auth
def test_auth_not_project(client: TestClient) -> None:
    response = client.get("/projects/")

    assert response.status_code == 200
    assert response.url == "http://testserver/"
