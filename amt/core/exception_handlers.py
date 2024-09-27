import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from amt.api.deps import templates
from amt.core.exceptions import AMTHTTPException, AMTNotFound, AMTRepositoryError
from amt.core.internationalization import (
    get_current_translation,
)

logger = logging.getLogger(__name__)


async def general_exception_handler(request: Request, exc: Exception) -> HTMLResponse:
    exception_name = exc.__class__.__name__

    logger.debug(f"general_exception_handler {exception_name}: {exc}")

    translations = get_current_translation(request)

    message = None
    if isinstance(exc, AMTRepositoryError | AMTHTTPException):
        message = exc.getmessage(translations)
    elif isinstance(exc, StarletteHTTPException):
        message = AMTNotFound().getmessage(translations) if exc.status_code == status.HTTP_404_NOT_FOUND else exc.detail
    elif isinstance(exc, RequestValidationError):
        messages: list[str] = [f"{error['loc'][-1]}: {error['msg']}" for error in exc.errors()]
        message = "\n".join(messages)

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(exc, StarletteHTTPException):
        status_code = exc.status_code
    elif isinstance(exc, RequestValidationError):
        status_code = status.HTTP_400_BAD_REQUEST

    # todo: what if request.state.htmx does not exist?
    template_name = (
        f"errors/_{exception_name}_{status_code}.html.j2"
        if request.state.htmx
        else f"errors/{exception_name}_{status_code}.html.j2"
    )
    fallback_template_name = "errors/_Exception.html.j2" if request.state.htmx else "errors/Exception.html.j2"

    response: HTMLResponse | None = None

    try:
        response = templates.TemplateResponse(
            request,
            template_name,
            {"message": message},
            status_code=status_code,
        )
    except Exception:
        response = templates.TemplateResponse(
            request,
            fallback_template_name,
            {"message": message},
            status_code=status_code,
        )

    return response
