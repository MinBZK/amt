from fastapi.testclient import TestClient


def test_get_main_page(client: TestClient) -> None:
    response = client.get("/pages/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"<!DOCTYPE html>" in response.content
