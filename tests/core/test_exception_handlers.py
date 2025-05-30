import pytest
from amt.core.exception_handlers import translate_pydantic_exception
from amt.schema.algorithm import AlgorithmNew
from babel.support import NullTranslations
from fastapi import status
from httpx import AsyncClient

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
