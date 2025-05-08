import logging
import typing

from fastapi_csrf_protect import CsrfProtect  # type: ignore
from fastapi_csrf_protect.exceptions import CsrfProtectError, MissingTokenError, TokenValidationError  # type: ignore
from itsdangerous import BadData, SignatureExpired, URLSafeTimedSerializer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from amt.core.csrf import get_csrf_config  # type: ignore # noqa
from amt.core.exception_handlers import general_exception_handler
from amt.core.exceptions import AMTCSRFProtectError

RequestResponseEndpoint = typing.Callable[[Request], typing.Awaitable[Response]]


logger = logging.getLogger(__name__)


class CookieOnlyCsrfProtect(CsrfProtect):
    """
    We can not use the header + cookie CSRF at this moment, there are too many dynamically
    loaded components (through htmx) where header keys cause mismatches. For now, we will use cookie
    verification using this class based on the original CsrfProtect.
    """

    async def validate_csrf(
        self,
        request: Request,
        cookie_key: str | None = None,
        secret_key: str | None = None,
        time_limit: int | None = None,
    ) -> None:
        secret_key = secret_key or self._secret_key
        if secret_key is None:
            raise RuntimeError("A secret key is required to use CsrfProtect extension.")

        cookie_key = cookie_key or self._cookie_key
        signed_token = request.cookies.get(cookie_key)

        if signed_token is None:
            raise MissingTokenError(f"Missing Cookie: `{cookie_key}`.")

        time_limit = time_limit or self._max_age
        serializer = URLSafeTimedSerializer(secret_key, salt="fastapi-csrf-token")
        try:
            serializer.loads(signed_token, max_age=time_limit)
        except SignatureExpired as e:
            raise TokenValidationError("The CSRF token has expired.") from e
        except BadData as e:
            raise TokenValidationError("The CSRF token is invalid.") from e


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    This middleware implements CSRF protection through FastAPI CSRF Protect.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.csrf_protect = CookieOnlyCsrfProtect()
        self.safe_methods = ("GET", "HEAD", "OPTIONS", "TRACE")

    def _include_request(self, request: Request) -> bool:
        """
        This method specifies whether a request should be protected by FastAPI CSRF Protect or not.
        """
        is_not_static_and_asset: bool = "static" not in request.url.path and "assets" not in request.url.path
        is_not_htmx: bool = request.state.htmx == "False"
        return is_not_static_and_asset or is_not_htmx  # or is_not_assets

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        signed_token = ""

        if self._include_request(request):
            request.state.csrftoken = ""

            if request.method in self.safe_methods:
                csrf_token, signed_token = self.csrf_protect.generate_csrf_tokens()
                logger.debug(f"generating tokens: csrf_token={csrf_token}, signed_token={signed_token}")
                request.state.csrftoken = csrf_token
            else:
                csrf_token = request.headers.get("X-CSRF-Token", "")
                logger.debug(f"validating tokens: csrf_token={csrf_token}")
                await self.csrf_protect.validate_csrf(request)

        response = await call_next(request)

        if self._include_request(request) and request.method in self.safe_methods:  # noqa
            # TODO FIXME (Robbert) we always set the cookie, this causes CSRF problems
            if request.url.path != "/organizations/users":
                self.csrf_protect.set_csrf_cookie(signed_token, response)
                logger.debug(f"set csrf_cookie: signed_token={signed_token}")

        return response


class CSRFMiddlewareExceptionHandler(BaseHTTPMiddleware):
    """
    This middleware is necessary to propagate CsrfProtectErrors to the csrf_protection_handler.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            response = await call_next(request)
        except CsrfProtectError:
            # middleware exceptions are not handled by the fastapi error handlers, so we call the function ourselves
            return await general_exception_handler(request, AMTCSRFProtectError())
        return response
