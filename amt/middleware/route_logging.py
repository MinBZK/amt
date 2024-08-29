import logging
import typing
from time import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from ulid import ULID

from amt.utils.mask import Mask

RequestResponseEndpoint = typing.Callable[[Request], typing.Awaitable[Response]]

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_time = time()
        request_id: str = str(ULID())
        masker = Mask(mask_keywords=["cookie"])
        request.state.request_id = request_id

        response = await call_next(request)
        response_time = time()

        response.headers["X-API-Request-ID"] = request_id
        masked_request_headers = masker.secrets(dict(request.headers))
        masked_response_headers = masker.secrets(dict(response.headers))

        logging_body = {
            "request_id": request_id,
            "request": {
                "time": request_time,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "headers": masked_request_headers,
            },
            "response": {
                "time": response_time,
                "status_code": response.status_code,
                "headers": masked_response_headers,
            },
            "duration": (response_time - request_time) * 1000,
        }

        logger.debug(logging_body)
        return response
