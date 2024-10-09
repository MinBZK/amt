import os
import typing

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from amt.core.authorization import get_user
from amt.core.exceptions import AMTAuthorizationError

RequestResponseEndpoint = typing.Callable[[Request], typing.Awaitable[Response]]


class AuthorizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path.startswith("/static/"):
            return await call_next(request)

        user = get_user(request)
        if user:  # pragma: no cover
            return await call_next(request)

        response = await call_next(request)

        if hasattr(request.state, "noauth"):
            return response

        auth_disable: bool = bool(os.environ.get("DISABLE_AUTH", False))

        if auth_disable:
            return response

        raise AMTAuthorizationError()
