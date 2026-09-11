from typing import Any

import pytest
from amt.core.exception_handlers import general_exception_handler, translate_pydantic_exception
from amt.core.exceptions import AMTStorageError
from amt.schema.algorithm import AlgorithmNew
from babel.support import NullTranslations
from fastapi import status
from httpx import AsyncClient
from starlette.requests import Request
from starlette.responses import Response

from tests.conftest import amt_vcr


@pytest.mark.asyncio
async def test_http_exception_handler(client: AsyncClient):
    response = await client.get("/raise-http-exception")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_request_validation_exception_handler(client: AsyncClient):
    response = await client.get("/algorithms/?skip=a")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_request_csrf_protect_exception.yml")  # type: ignore
@pytest.mark.skip(reason="we do not check headers at the moment")
async def test_request_csrf_protect_exception_handler_invalid_token_in_header(client: AsyncClient):
    data = await client.get("/algorithms/new")
    new_algorithm = AlgorithmNew(
        name="default algorithm", lifecycle="DATA_EXPLORATION_AND_PREPARATION", organization_id=1
    )
    response = await client.post(
        "/algorithms/new",
        json=new_algorithm.model_dump(),
        headers={"X-CSRF-Token": "1"},
        cookies=data.cookies,
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_http_exception_handler_htmx(client: AsyncClient):
    response = await client.get("/raise-http-exception", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_request_validation_exception_handler_htmx(client: AsyncClient):
    response = await client.get("/algorithms/?skip=a", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_request_csrf_protect_exception_handler_invalid_token.yml")  # type: ignore
async def test_request_csrf_protect_exception_handler_invalid_token(client: AsyncClient):
    await client.get("/algorithms/new")
    new_algorithm = AlgorithmNew(
        name="default algorithm", lifecycle="DATA_EXPLORATION_AND_PREPARATION", organization_id=1
    )
    client.cookies.clear()
    response = await client.post(
        "/algorithms/new",
        json=new_algorithm.model_dump(),
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_translate_pydantic_exception(client: AsyncClient) -> None:
    response = translate_pydantic_exception(err={"msg": "test", "type": "nonexistent"}, translations=NullTranslations())
    assert response == "test"


def _htmx_request() -> Request:
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": [], "query_string": b""})
    request.state.htmx = True
    return request


async def _render(response: Response) -> str:
    """Drive the ASGI interface, because these template responses render on call, not on init."""

    async def receive() -> Any:  # noqa: ANN401
        return {"type": "http.disconnect"}

    async def send(message: Any) -> None:  # noqa: ANN401
        pass

    await response({"type": "http"}, receive, send)
    return bytes(response.body).decode()


@pytest.mark.asyncio
async def test_htmx_error_without_own_template_renders_the_alert():
    """An AMT exception retargeted to the alert container must render the alert, not a bare paragraph.

    AMTStorageError has no template of its own, so this exercises the fallback.
    """
    response = await general_exception_handler(_htmx_request(), AMTStorageError())
    body = await _render(response)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert 'id="general-error-content"' in body
    assert "rvo-alert--error" in body
