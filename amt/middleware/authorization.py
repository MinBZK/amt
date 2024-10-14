import os
import typing

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from amt.core.authorization import get_user

RequestResponseEndpoint = typing.Callable[[Request], typing.Awaitable[Response]]


class AuthorizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in ["/auth/login", "/auth/logout", "/auth/callback", "/health/live", "/health/ready", "/"]:
            return await call_next(request)

        if request.url.path.startswith("/static/"):
            return await call_next(request)

        user = get_user(request)
        if user:  # pragma: no cover
            return await call_next(request)

        response = await call_next(request)

        auth_disable: bool = bool(os.environ.get("DISABLE_AUTH", False))

        if auth_disable:
            return response

        return RedirectResponse(url="/")
