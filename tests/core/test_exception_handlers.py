from fastapi import status
from fastapi.testclient import TestClient


def test_http_exception_handler(client: TestClient):
    response = client.get("/raise-http-exception")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.headers["content-type"] == "text/html; charset=utf-8"


def test_request_validation_exception_handler(client: TestClient):
    response = client.get("/projects/?skip=a")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.headers["content-type"] == "text/html; charset=utf-8"


def test_http_exception_handler_htmx(client: TestClient):
    response = client.get("/raise-http-exception", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.headers["content-type"] == "text/html; charset=utf-8"


def test_request_validation_exception_handler_htmx(client: TestClient):
    response = client.get("/projects/?skip=a", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.headers["content-type"] == "text/html; charset=utf-8"
