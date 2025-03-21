import logging
from enum import Enum
from typing import TypeVar

from jinja2 import StrictUndefined, Undefined
from starlette.requests import Request

from amt.api.editable_util import (
    is_editable_resource,
    is_parent_editable,
    replace_digits_in_brackets,
    resolve_resource_list_path,
)
from amt.api.http_browser_caching import url_for_cache
from amt.api.localizable import LocalizableEnum
from amt.api.navigation import NavigationItem, get_main_menu
from amt.api.routes.shared import (
    get_localized_value,
    is_nested_enum,
    is_path_with_list,
    nested_enum,
    nested_enum_value,
    nested_value,
)
from amt.api.template_classes import LocaleJinja2Templates
from amt.core.authorization import AuthorizationVerb, get_user
from amt.core.config import VERSION, get_settings
from amt.core.internationalization import (
    format_datetime,
    format_timedelta,
    get_current_translation,
    get_dynamic_field_translations,
    get_requested_language,
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


def permission(permission: str, verb: AuthorizationVerb, permissions: dict[str, list[AuthorizationVerb]]) -> bool:
    authorized = False

    if permission in permissions and verb in permissions[permission]:
        authorized = True

    return authorized


def instance(obj: object, type_str: str) -> bool:
    match type_str:
        case "str":
            return isinstance(obj, str)
        case "list":
            return isinstance(obj, list)
        case "IterMixin":
            return isinstance(obj, IterMixin)
        case "dict":
            return isinstance(obj, dict)
        case _:
            raise TypeError("Unsupported type: " + type_str)


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


def equal_or_includes(my_value: str, check_against_value: str | list[str] | tuple[str]) -> bool:
    """Test if my_value equals or exists in check_against_value"""
    if isinstance(check_against_value, list | tuple):
        return my_value in check_against_value
    elif isinstance(check_against_value, str):
        return my_value == check_against_value
    return False


templates = LocaleJinja2Templates(
    directory="amt/site/templates/", context_processors=[custom_context_processor], undefined=get_undefined_behaviour()
)
templates.env.filters.update(  # pyright: ignore [reportUnknownMemberType]
    {
        "format_datetime": format_datetime,
        "format_timedelta": format_timedelta,
        "time_ago": time_ago,
    }
)
templates.env.globals.update(  # pyright: ignore [reportUnknownMemberType]
    {
        "url_for_cache": url_for_cache,
        "nested_value": nested_value,
        "is_nested_enum": is_nested_enum,
        "nested_enum": nested_enum,
        "nested_enum_value": nested_enum_value,
        "isinstance": instance,
        "is_editable_resource": is_editable_resource,
        "replace_digits_in_brackets": replace_digits_in_brackets,
        "permission": permission,
        "hasattr": hasattr_jinja,
        "is_path_with_list": is_path_with_list,
        "is_parent_editable": is_parent_editable,
        "resolve_resource_list_path": resolve_resource_list_path,
        "get_localized_value": get_localized_value,
    }
)
# env tests allows for usage in templates like: if value is test_name(other_value)
templates.env.tests.update(  # pyright: ignore [reportUnknownMemberType]
    {"permission": permission, "equal_or_includes": equal_or_includes}
)


templates.env.add_extension("jinja2_base64_filters.Base64Filters")  # pyright: ignore [reportUnknownMemberType]
