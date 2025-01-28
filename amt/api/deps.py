import logging
import re
from collections.abc import Sequence
from enum import Enum
from os import PathLike
from pyclbr import Class
from typing import Any, AnyStr, TypeVar

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, StrictUndefined, Undefined
from starlette.background import BackgroundTask
from starlette.templating import _TemplateResponse  # pyright: ignore [reportPrivateUsage]

from amt.api.editable import ResolvedEditable
from amt.api.http_browser_caching import url_for_cache
from amt.api.localizable import LocalizableEnum
from amt.api.navigation import NavigationItem, get_main_menu
from amt.api.routes.shared import is_nested_enum, nested_enum, nested_enum_value, nested_value
from amt.core.authorization import AuthorizationVerb, get_user
from amt.core.config import VERSION, get_settings
from amt.core.internationalization import (
    format_datetime,
    format_timedelta,
    get_current_translation,
    get_dynamic_field_translations,
    get_requested_language,
    get_supported_translation,
    get_translation,
    supported_translations,
    time_ago,
)
from amt.schema.shared import IterMixin
from amt.schema.webform import WebFormFieldType

T = TypeVar("T", bound=Enum | LocalizableEnum)

logger = logging.getLogger(__name__)


def custom_context_processor(
    request: Request,
) -> dict[str, str | None | list[str] | dict[str, str] | list[NavigationItem] | type[WebFormFieldType]]:
    lang = get_requested_language(request)
    translations = get_current_translation(request)
    permissions = getattr(request.state, "permissions", {})

    return {
        "version": VERSION,
        "available_translations": list(supported_translations),
        "language": lang,
        "translations": get_dynamic_field_translations(lang),
        "main_menu_items": get_main_menu(request, translations),
        "user": get_user(request),
        "permissions": permissions,
        "WebFormFieldType": WebFormFieldType,
    }


def get_undefined_behaviour() -> type[Undefined]:
    return StrictUndefined if get_settings().DEBUG else Undefined


def replace_digits_in_brackets(string: str) -> str:
    return re.sub(r"\[(\d+)]", "[*]", string)


def is_editable_resource(full_resource_path: str, editables: dict[str, ResolvedEditable]) -> bool:
    return replace_digits_in_brackets(full_resource_path) in editables


def permission(permission: str, verb: AuthorizationVerb, permissions: dict[str, list[AuthorizationVerb]]) -> bool:
    authorized = False

    if permission in permissions and verb in permissions[permission]:
        authorized = True

    return authorized


# we use a custom override so we can add the translation per request, which is parsed in the Request object in kwargs
class LocaleJinja2Templates(Jinja2Templates):
    def _create_env(
        self,
        directory: str | PathLike[AnyStr] | Sequence[str | PathLike[AnyStr]],
        **env_options: Any,  # noqa: ANN401
    ) -> Environment:
        env: Environment = super()._create_env(directory, **env_options)  # pyright: ignore [reportUnknownMemberType, reportUnknownVariableType, reportArgumentType]
        env.add_extension("jinja2.ext.i18n")  # pyright: ignore [reportUnknownMemberType]
        return env  # pyright: ignore [reportUnknownVariableType]

    def TemplateResponse(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        request: Request,
        name: str,
        context: dict[str, Any] | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> _TemplateResponse:
        content_language = get_supported_translation(get_requested_language(request))
        translations = get_translation(content_language)
        if headers is None:
            headers = {}
        headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        if "Content-Language" not in headers:
            headers["Content-Language"] = ",".join(supported_translations)
        self.env.install_gettext_translations(translations, newstyle=True)  # pyright: ignore [reportUnknownMemberType]

        if context is None:
            context = {}

        if hasattr(request.state, "csrftoken"):
            context["csrftoken"] = request.state.csrftoken
        else:
            context["csrftoken"] = ""

        return super().TemplateResponse(request, name, context, status_code, headers, media_type, background)

    def Redirect(self, request: Request, url: str) -> HTMLResponse:
        headers = {"HX-Redirect": url}
        return self.TemplateResponse(request, "redirect.html.j2", headers=headers)


def instance(obj: Class, type_string: str) -> bool:
    match type_string:
        case "str":
            return isinstance(obj, str)
        case "list":
            return isinstance(obj, list)
        case "IterMixin":
            return isinstance(obj, IterMixin)
        case "dict":
            return isinstance(obj, dict)
        case _:
            raise TypeError("Unsupported type: " + type_string)


def hasattr_jinja(obj: object, attributes: str) -> bool:
    """
    Convenience method that checks whether an object has the given attributes.
    :param obj: the object to check
    :param attributes: the attributes, seperated by dots, like field1.field2.field3
    :return: True if the object has the given attribute and its value is not None, False otherwise
    """
    for attribute in attributes.split("."):
        if hasattr(obj, attribute) and getattr(obj, attribute) is not None:
            obj = getattr(obj, attribute)
        else:
            return False
    return True


templates = LocaleJinja2Templates(
    directory="amt/site/templates/", context_processors=[custom_context_processor], undefined=get_undefined_behaviour()
)
templates.env.filters["format_datetime"] = format_datetime  # pyright: ignore [reportUnknownMemberType]
templates.env.filters["format_timedelta"] = format_timedelta  # pyright: ignore [reportUnknownMemberType]
templates.env.filters["time_ago"] = time_ago  # pyright: ignore [reportUnknownMemberType]
templates.env.globals.update(url_for_cache=url_for_cache)  # pyright: ignore [reportUnknownMemberType]
templates.env.globals.update(nested_value=nested_value)  # pyright: ignore [reportUnknownMemberType]
templates.env.globals.update(is_nested_enum=is_nested_enum)  # pyright: ignore [reportUnknownMemberType]
templates.env.globals.update(nested_enum=nested_enum)  # pyright: ignore [reportUnknownMemberType]
templates.env.globals.update(nested_enum_value=nested_enum_value)  # pyright: ignore [reportUnknownMemberType]
templates.env.globals.update(isinstance=instance)  # pyright: ignore [reportUnknownMemberType]
templates.env.globals.update(is_editable_resource=is_editable_resource)  # pyright: ignore [reportUnknownMemberType]
templates.env.globals.update(replace_digits_in_brackets=replace_digits_in_brackets)  # pyright: ignore [reportUnknownMemberType]
templates.env.globals.update(permission=permission)  # pyright: ignore [reportUnknownMemberType]
templates.env.globals.update(hasattr=hasattr_jinja)  # pyright: ignore [reportUnknownMemberType]
templates.env.tests["permission"] = permission  # pyright: ignore [reportUnknownMemberType]
templates.env.add_extension("jinja2_base64_filters.Base64Filters")  # pyright: ignore [reportUnknownMemberType]
