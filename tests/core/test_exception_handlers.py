import pytest
from amt.core.exceptions import AMTCSRFProtectError
from amt.schema.project import ProjectNew
from fastapi import status
from httpx import AsyncClient


async def test_http_exception_handler(client: AsyncClient):
    response = await client.get("/raise-http-exception")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.headers["content-type"] == "text/html; charset=utf-8"


async def test_request_validation_exception_handler(client: AsyncClient):
    response = await client.get("/algorithm-systems/?skip=a")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.headers["content-type"] == "text/html; charset=utf-8"


async def test_request_csrf_protect_exception_handler_invalid_token_in_header(client: AsyncClient):
    data = await client.get("/algorithm-systems/new")
    new_project = ProjectNew(name="default project", lifecycle="DATA_EXPLORATION_AND_PREPARATION")
    with pytest.raises(AMTCSRFProtectError):
        _response = client.post(
            "/algorithm-systems/new", json=new_project.model_dump(), headers={"X-CSRF-Token": "1"}, cookies=data.cookies
        )


async def test_http_exception_handler_htmx(client: AsyncClient):
    response = await client.get("/raise-http-exception", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.headers["content-type"] == "text/html; charset=utf-8"


async def test_request_validation_exception_handler_htmx(client: AsyncClient):
    response = await client.get("/algorithm-systems/?skip=a", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.headers["content-type"] == "text/html; charset=utf-8"


async def test_request_csrf_protect_exception_handler_invalid_token(client: AsyncClient):
    data = await client.get("/algorithm-systems/new")
    new_project = ProjectNew(name="default project", lifecycle="DATA_EXPLORATION_AND_PREPARATION")
    with pytest.raises(AMTCSRFProtectError):
        _response = client.post(
            "/algorithm-systems/new",
            json=new_project.model_dump(),
            headers={"HX-Request": "true", "X-CSRF-Token": "1"},
            cookies=data.cookies,
        )


async def test_(client: AsyncClient):
    response = await client.get("/algorithm-systems/?skip=a", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.headers["content-type"] == "text/html; charset=utf-8"
