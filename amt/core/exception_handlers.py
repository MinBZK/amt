import logging
from gettext import gettext as _
from json import JSONDecodeError
from typing import Any

from babel.support import NullTranslations
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from amt.api.deps import templates
from amt.core.exceptions import AMTCSRFProtectError, AMTHTTPException, AMTNotFound, AMTRepositoryError
from amt.core.internationalization import (
    get_current_translation,
)

logger = logging.getLogger(__name__)

CUSTOM_MESSAGES = {
    "string_too_short": _("String should have at least {min_length} characters"),
    "missing": _("Field required"),
    "value_error": _("Field required"),
    "string_pattern_mismatch": _("String should match pattern '{pattern}'"),
    "int_parsing": _("Input should be a valid integer."),
    "maintainer_role_required_with_context": _(
        "For {type} {type_name}, at least one member must have the maintainer role."
    ),
    "maintainer_role_required": _("At least one member must have the maintainer role."),
}


def translate_pydantic_exception(err: dict[str, Any], translations: NullTranslations) -> str:
    message: str | None = CUSTOM_MESSAGES.get(err["type"], None)

    if message:
        custom_message = translations.gettext(message)
        return custom_message.format(**err["ctx"]) if "ctx" in err else custom_message

    return err["msg"]


async def general_exception_handler(request: Request, exc: Exception) -> HTMLResponse:  # noqa
    exception_name = exc.__class__.__name__

    logger.exception(f"general_exception_handler {exception_name}: {exc}")

    translations = get_current_translation(request)

    response_headers: dict[str, str] = {}
    message = None
    if isinstance(exc, AMTCSRFProtectError):  # AMTCSRFProtectError is AMTHTTPException
        message = exc.getmessage(translations)
        response_headers["HX-Retarget"] = "#general-error-container"
    elif isinstance(exc, AMTRepositoryError | AMTHTTPException):
        message = exc.getmessage(translations)
        # we assume a generic error div is targeted by id, so we want to replace the inner content
        response_headers["HX-Reswap"] = "innerHTML"
        response_headers["HX-Retarget"] = "#general-error-container"
    elif isinstance(exc, StarletteHTTPException):
        message = AMTNotFound().getmessage(translations) if exc.status_code == status.HTTP_404_NOT_FOUND else exc.detail
    elif isinstance(exc, RequestValidationError):
        # I assume only pydantic errors get into this section
        message = exc.errors()
        for err in message:
            err["msg"] = translate_pydantic_exception(err, translations)
        # Errors should be handled in appropriate "containers",
        #  so we always want to replace the content and not the container
        response_headers["HX-Reswap"] = "innerHTML"

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(exc, StarletteHTTPException):
        status_code = exc.status_code
    elif isinstance(exc, RequestValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, JSONDecodeError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

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
            request, template_name, {"message": message}, status_code=status_code, headers=response_headers
        )
    except Exception:
        logger.warning(
            "Can not display error template " + template_name + " as it does not exist, using fallback template"
        )
        response = templates.TemplateResponse(
            request,
            fallback_template_name,
            {"message": message},
            status_code=status_code,
            headers=response_headers,
        )

    return response
