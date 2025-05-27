import pytest
from amt.server import create_app
from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from pytest_mock import MockerFixture
from starlette.exceptions import HTTPException


@pytest.mark.asyncio
async def test_create_app() -> None:
    # given/when
    app = create_app()

    # then
    assert app is not None
    assert app.title == "AMT"
    assert len(app.routes) > 0
    assert app.middleware is not None


@pytest.mark.asyncio
async def test_http_exception_handler(mocker: MockerFixture) -> None:
    # given
    mock_general_handler = mocker.patch(
        "amt.server.amt_general_exception_handler",
        return_value=Response(content="Error handled", status_code=500),
    )

    app = create_app()
    request = Request({"type": "http"})
    exception = HTTPException(status_code=404, detail="Not Found")

    # when
    handler = app.exception_handlers[HTTPException]
    response = await handler(request, exception)  # pyright: ignore[reportUnknownVariableType, reportGeneralTypeIssues]

    # then
    assert response.status_code == 500  # pyright: ignore[reportUnknownMemberType]
    assert mock_general_handler.called
    assert mock_general_handler.call_args[0][0] == request
    assert mock_general_handler.call_args[0][1] == exception


@pytest.mark.asyncio
async def test_validation_exception_handler(mocker: MockerFixture) -> None:
    # given
    mock_general_handler = mocker.patch(
        "amt.server.amt_general_exception_handler",
        return_value=Response(content="Validation error handled", status_code=422),
    )

    app = create_app()
    request = Request({"type": "http"})
    exception = RequestValidationError(
        errors=[{"loc": ["body"], "msg": "Field required", "type": "value_error.missing"}]
    )

    # when
    handler = app.exception_handlers[RequestValidationError]
    response = await handler(request, exception)  # pyright: ignore[reportUnknownVariableType, reportGeneralTypeIssues]

    # then
    assert response.status_code == 422  # pyright: ignore[reportUnknownMemberType]
    assert mock_general_handler.called
    assert mock_general_handler.call_args[0][0] == request
    assert mock_general_handler.call_args[0][1] == exception


@pytest.mark.asyncio
async def test_general_exception_handler(mocker: MockerFixture) -> None:
    # given
    mock_general_handler = mocker.patch(
        "amt.server.amt_general_exception_handler",
        return_value=Response(content="General error handled", status_code=500),
    )

    app = create_app()
    request = Request({"type": "http"})
    exception = ValueError("Some random error")

    # when
    handler = app.exception_handlers[Exception]
    response = await handler(request, exception)  # pyright: ignore[reportUnknownVariableType, reportGeneralTypeIssues]

    # then
    assert response.status_code == 500  # pyright: ignore[reportUnknownMemberType]
    assert mock_general_handler.called
    assert mock_general_handler.call_args[0][0] == request
    assert mock_general_handler.call_args[0][1] == exception


@pytest.mark.asyncio
async def test_app_lifespan(mocker: MockerFixture) -> None:
    # given
    mock_check_db = mocker.patch("amt.server.check_db")
    mock_init_db = mocker.patch("amt.server.init_db")
    # Instead of mocking logging completely, just confirm the check_db and init_db were called

    from amt.server import lifespan

    app = create_app()

    # when
    async with lifespan(app):
        # then
        mock_check_db.assert_called_once()
        mock_init_db.assert_called_once()
