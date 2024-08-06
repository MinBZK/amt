import logging
import typing

from fastapi_csrf_protect import CsrfProtect  # type: ignore
from fastapi_csrf_protect.exceptions import CsrfProtectError  # type: ignore
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from amt.core.csrf import get_csrf_config  # type: ignore # noqa
from amt.core.exception_handlers import csrf_protect_exception_handler

RequestResponseEndpoint = typing.Callable[[Request], typing.Awaitable[Response]]


logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    This middleware implements CSRF signed double token protection through FastAPI CSRF Protect.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.csrf_protect = CsrfProtect()
        self.safe_methods = ("GET", "HEAD", "OPTIONS", "TRACE")

    def _include_request(self, request: Request) -> bool:
        """
        This method specifies whether a request should be protected by FastAPI CSRF Protect or not.
        The method is needed because we need to in any case exclude GET requests originating from
        HTMX or GET requests that fetch static pages becauses this will result in multiple tokens
        which make validation impossible due to the asynchronisity of the requests.
        """
        is_not_static: bool = "static" not in request.url.path
        is_not_htmx: bool = request.state.htmx == "False"
        return is_not_static or is_not_htmx

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        signed_token = ""
        if self._include_request(request):
            request.state.csrftoken = ""
            if request.method in self.safe_methods:
                csrf_token, signed_token = self.csrf_protect.generate_csrf_tokens()
                logger.debug(f"generating tokens: csrf_token={csrf_token}, signed_token={signed_token}")
                request.state.csrftoken = csrf_token
            else:
                csrf_token = request.headers["X-CSRF-Token"]
                logger.debug(f"validating tokens: csrf_token={csrf_token}")
                await self.csrf_protect.validate_csrf(request)

        response = await call_next(request)

        if self._include_request(request) and request.method in self.safe_methods:
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
        except CsrfProtectError as e:
            return await csrf_protect_exception_handler(request, e)
        return response
