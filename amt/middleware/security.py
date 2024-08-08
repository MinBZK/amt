import typing

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

RequestResponseEndpoint = typing.Callable[[Request], typing.Awaitable[Response]]


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        response.headers["Strict-Transport-Security"] = "Strict-Transport-Security: max-age=31536000; includeSubDomains"

        return response
