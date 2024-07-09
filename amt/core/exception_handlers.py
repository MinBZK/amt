import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse:
    logger.debug(f"http_exception_handler: {exc.status_code} - {exc.detail}")
    return HTMLResponse(
        status_code=exc.status_code,
        content=f"<p>{exc.detail}</p>",
    )


async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> HTMLResponse:
    logger.debug(f"validation_exception_handler: {exc.errors()}")
    errors = exc.errors()
    messages: list[str] = [f"{error['loc'][-1]}: {error['msg']}" for error in errors]

    return HTMLResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=f"<h1>Invalid Request</h1><p>{messages}</p>",
    )
