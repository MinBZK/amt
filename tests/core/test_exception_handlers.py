import pytest
from amt.core.exceptions import AMTCSRFProtectError
from amt.schema.project import ProjectNew
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


def test_request_csrf_protect_exception_handler_invalid_token_in_header(client: TestClient):
    data = client.get("/projects/new")
    new_project = ProjectNew(name="default project", lifecycle="DATA_EXPLORATION_AND_PREPARATION")
    with pytest.raises(AMTCSRFProtectError):
        _response = client.post(
            "/projects/new", json=new_project.model_dump(), headers={"X-CSRF-Token": "1"}, cookies=data.cookies
        )


def test_http_exception_handler_htmx(client: TestClient):
    response = client.get("/raise-http-exception", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.headers["content-type"] == "text/html; charset=utf-8"


def test_request_validation_exception_handler_htmx(client: TestClient):
    response = client.get("/projects/?skip=a", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.headers["content-type"] == "text/html; charset=utf-8"


def test_request_csrf_protect_exception_handler_invalid_token(client: TestClient):
    data = client.get("/projects/new")
    new_project = ProjectNew(name="default project", lifecycle="DATA_EXPLORATION_AND_PREPARATION")
    with pytest.raises(AMTCSRFProtectError):
        _response = client.post(
            "/projects/new",
            json=new_project.model_dump(),
            headers={"HX-Request": "true", "X-CSRF-Token": "1"},
            cookies=data.cookies,
        )


def test_(client: TestClient):
    response = client.get("/projects/?skip=a", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.headers["content-type"] == "text/html; charset=utf-8"
