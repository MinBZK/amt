from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return HTMLResponse(
        status_code=exc.status_code,
        content=f"<h1>{exc.status_code}</h1><p>{exc.detail}</p>",
    )


async def validation_exception_handler(_request: Request, _exc: RequestValidationError):
    return HTMLResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content="<h1>{status.HTTP_400_BAD_REQUEST}</h1><p>Invalid Request</p>",
    )
