from typing import Any  # pyright: ignore[reportUnusedImport]

# pyright: reportMissingTypeStubs=false
import pytest
from amt.middleware.csrf import (
    CookieOnlyCsrfProtect,
    CSRFMiddleware,
)
from fastapi import FastAPI, Request
from fastapi_csrf_protect.exceptions import (
    MissingTokenError,
    TokenValidationError,
)
from itsdangerous import BadData, SignatureExpired
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_cookie_only_csrf_protect_validate_csrf_missing_token(mocker: MockerFixture) -> None:
    # given
    csrf_protect = CookieOnlyCsrfProtect()
    # Use mocker to modify the instance attributes instead of directly setting them
    mocker.patch.object(csrf_protect, "_secret_key", "test-secret")
    mocker.patch.object(csrf_protect, "_cookie_key", "csrf_token")

    scope: dict[str, Any] = {
        "type": "http",
        "headers": [],
    }
    request = Request(scope)

    # when/then
    with pytest.raises(MissingTokenError, match=r"Missing Cookie: `csrf_token`."):
        await csrf_protect.validate_csrf(request)


@pytest.mark.asyncio
async def test_cookie_only_csrf_protect_validate_csrf_expired_token(mocker: MockerFixture) -> None:
    # given
    csrf_protect = CookieOnlyCsrfProtect()
    # Use mocker to modify the instance attributes instead of directly setting them
    mocker.patch.object(csrf_protect, "_secret_key", "test-secret")
    mocker.patch.object(csrf_protect, "_cookie_key", "csrf_token")

    scope: dict[str, Any] = {
        "type": "http",
        "headers": [(b"cookie", b"csrf_token=expired_token")],
    }
    request = Request(scope)

    # Mock the serializer to raise SignatureExpired
    mock_serializer = mocker.Mock()
    mock_serializer.loads.side_effect = SignatureExpired("Expired")
    mocker.patch("amt.middleware.csrf.URLSafeTimedSerializer", return_value=mock_serializer)

    # when/then
    with pytest.raises(TokenValidationError, match=r"The CSRF token has expired."):
        await csrf_protect.validate_csrf(request)


@pytest.mark.asyncio
async def test_cookie_only_csrf_protect_validate_csrf_invalid_token(mocker: MockerFixture) -> None:
    # given
    csrf_protect = CookieOnlyCsrfProtect()
    # Use mocker to modify the instance attributes instead of directly setting them
    mocker.patch.object(csrf_protect, "_secret_key", "test-secret")
    mocker.patch.object(csrf_protect, "_cookie_key", "csrf_token")

    scope: dict[str, Any] = {
        "type": "http",
        "headers": [(b"cookie", b"csrf_token=invalid_token")],
    }
    request = Request(scope)

    # Mock the serializer to raise BadData
    mock_serializer = mocker.Mock()
    mock_serializer.loads.side_effect = BadData("Bad data")
    mocker.patch("amt.middleware.csrf.URLSafeTimedSerializer", return_value=mock_serializer)

    # when/then
    with pytest.raises(TokenValidationError, match=r"The CSRF token is invalid."):
        await csrf_protect.validate_csrf(request)


@pytest.mark.asyncio
async def test_csrf_middleware_init() -> None:
    # given/when
    app = FastAPI()
    middleware = CSRFMiddleware(app)

    # then
    assert middleware.app == app
    assert isinstance(middleware.csrf_protect, CookieOnlyCsrfProtect)
    assert middleware.safe_methods == ("GET", "HEAD", "OPTIONS", "TRACE")
