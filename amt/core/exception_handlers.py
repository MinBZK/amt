import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi_csrf_protect.exceptions import CsrfProtectError  # type: ignore
from starlette.exceptions import HTTPException as StarletteHTTPException

from amt.api.deps import templates

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse:
    logger.debug(f"http_exception_handler: {exc.status_code} - {exc.detail}")

    if request.state.htmx:
        return templates.TemplateResponse(
            request,
            "errors/_HTTPException.html.j2",
            {"status_code": exc.status_code, "status_message": exc.detail},
            status_code=exc.status_code,
        )

    return templates.TemplateResponse(
        request,
        "errors/HTTPException.html.j2",
        {"status_code": exc.status_code, "status_message": exc.detail, "breadcrumbs": []},
        status_code=exc.status_code,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> HTMLResponse:
    logger.debug(f"validation_exception_handler: {exc.errors()}")
    errors = exc.errors()
    messages: list[str] = [f"{error['loc'][-1]}: {error['msg']}" for error in errors]

    if request.state.htmx:
        return templates.TemplateResponse(
            request,
            "errors/_RequestValidation.html.j2",
            {"message": messages},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return templates.TemplateResponse(
        request, "errors/RequestValidation.html.j2", {"message": messages}, status_code=status.HTTP_400_BAD_REQUEST
    )


async def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError) -> HTMLResponse:
    logger.debug(f"csrf_protect_exception_handler: {exc.status_code} - {exc.message}")

    if request.state.htmx:
        return templates.TemplateResponse(
            request,
            "errors/_CsrfProtectError.html.j2",
            {"status_code": exc.status_code, "message": exc.message},
            status_code=exc.status_code,
        )

    return templates.TemplateResponse(
        request,
        "errors/CsrfProtectError.html.j2",
        {"status_code": exc.status_code, "message": exc.message},
        status_code=exc.status_code,
    )
