import asyncio
import re
import threading
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import Any, T, cast  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType]

from pydantic import BaseModel
from starlette.requests import Request

from amt.api.editable_converters import StatusConverterForSystemcard
from amt.api.lifecycles import Lifecycles, get_localized_lifecycle
from amt.api.localizable import LocalizableEnum
from amt.api.organization_filter_options import OrganizationFilterOptions, get_localized_organization_filter
from amt.api.risk_group import RiskGroup, get_localized_risk_group
from amt.api.update_utils import extract_number_and_string
from amt.core.authorization import AuthorizationType
from amt.schema.localized_value_item import LocalizedValueItem
from amt.schema.shared import IterMixin
from amt.schema.webform_classes import WebFormOption
from amt.services.users import UsersService


async def get_filters_and_sort_by(
    request: Request, users_service: UsersService
) -> tuple[
    dict[str, AuthorizationType | str | int | list[str | int]], list[str], dict[str, LocalizedValueItem], dict[str, str]
]:
    active_filters: dict[str, str] = {
        k.removeprefix("active-filter-"): v
        for k, v in request.query_params.items()
        if k.startswith("active-filter") and v != ""
    }
    add_filters: dict[str, str] = {
        k.removeprefix("add-filter-"): v
        for k, v in request.query_params.items()
        if k.startswith("add-filter") and v != ""
    }
    # 'all organizations' is not really a filter type, so we remove it when it is added
    if "organization-type" in add_filters and add_filters["organization-type"] == OrganizationFilterOptions.ALL.value:
        del add_filters["organization-type"]
    drop_filters: list[str] = [v for k, v in request.query_params.items() if k.startswith("drop-filter") and v != ""]
    filters: dict[str, AuthorizationType | str | int | list[str | int]] = {
        k: v for k, v in (active_filters | add_filters).items() if k not in drop_filters
    }
    localized_filters: dict[str, LocalizedValueItem] = {}
    if "assignee" in filters:
        user_id = filters.get("assignee")
        user = await users_service.find_by_id(cast(str, user_id))
        if user is not None:
            localized_filters["assignee"] = LocalizedValueItem(display_value=user.name, value=str(user_id))
    localized_filters.update(
        {k: get_localized_value(k, cast(str, v), request) for k, v in filters.items() if k != "assignee"}
    )
    sort_by: dict[str, str] = {
        k.removeprefix("sort-by-"): v for k, v in request.query_params.items() if k.startswith("sort-by-") and v != ""
    }
    return filters, drop_filters, localized_filters, sort_by


def get_localized_value(key: str, value: str, request: Request) -> LocalizedValueItem:
    localized = None
    match key:
        case "lifecycle":
            if value in Lifecycles:
                localized = get_localized_lifecycle(Lifecycles(value), request)
            else:
                # we may need to convert the input value first (this is REALLY not the best way)
                convertor = StatusConverterForSystemcard()
                # the replace is a fix for bad lifecycle annotation in the algoritmekader
                converted_value: WebFormOption = run_async_function(convertor.read, value.replace("-", " "))  # pyright: ignore[reportUnknownVariableType]
                if converted_value.value in Lifecycles:  # pyright: ignore[reportUnknownMemberType]
                    localized = get_localized_lifecycle(Lifecycles(converted_value.value), request)  # pyright: ignore[reportUnknownMemberType]
        case "risk-group":
            localized = get_localized_risk_group(RiskGroup[value], request)
        case "organization-type":
            localized = get_localized_organization_filter(OrganizationFilterOptions(value), request)
        case _:
            localized = None

    if localized:
        return localized

    return LocalizedValueItem(value=value, display_value=f"Unknown [{value}]")


def get_nested(obj: Any, attr_path: str) -> Any:  # noqa: ANN401
    attrs = attr_path.lstrip("/").split("/") if "/" in attr_path else attr_path.lstrip(".").split(".")
    for attr in attrs:
        attr, index = extract_number_and_string(attr)
        if hasattr(obj, attr):  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
            obj = getattr(obj, attr)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        elif isinstance(obj, dict) and attr in obj:
            obj = obj[attr]  # pyright: ignore[reportUnknownVariableType]
        else:
            obj = None
            break
        if obj and index is not None:
            obj = obj[index]  # pyright: ignore[reportUnknownVariableType]
    return obj  # pyright: ignore[reportUnknownVariableType]


def nested_value(obj: Any, attr_path: str, default_value: str | list[str] | None = "") -> Any:  # noqa: ANN401
    obj = get_nested(obj, attr_path)
    if isinstance(obj, Enum):
        return obj.value
    if obj is None:
        return default_value
    return obj


def is_nested_enum(obj: Any, attr_path: str) -> bool:  # noqa: ANN401
    if not attr_path:
        return False
    obj = get_nested(obj, attr_path)
    return bool(isinstance(obj, Enum))


def nested_enum(obj: Any, attr_path: str, language: str) -> list[LocalizedValueItem]:  # noqa: ANN401
    nested_obj = get_nested(obj, attr_path)
    if not isinstance(nested_obj, LocalizableEnum):
        return []
    enum_class = type(nested_obj)
    return [e.localize(language) for e in enum_class if isinstance(e, LocalizableEnum)]


def nested_enum_value(obj: Any, attr_path: str, language: str) -> Any:  # noqa: ANN401
    return get_nested(obj, attr_path).localize(language)


def is_path_with_list(input_string: str) -> bool:
    """
    Checks if a string contains a number or wildcard within square brackets. Like /algorithm/1/labels[*].

    Returns:
        True if the string contains a number or wildcard in brackets, False otherwise.
    """
    return bool(re.search(r"\[(\d+|\*)]", input_string))


class UpdateFieldModel(BaseModel):
    value: str


# TODO: fix this method
def replace_none_with_empty_string_inplace(obj: dict[Any, Any] | list[Any] | IterMixin) -> None:  # noqa: C901
    """
    Recursively replaces all None values within a list, dict,
    or an IterMixin (class) object with an empty string.
    This function modifies the object in-place.

    Args:
      obj: The input object, which can be a list, dict, or an IterMixin (class) object.
    """
    if isinstance(obj, list):
        for i, item in enumerate(obj):
            if item is None:
                obj[i] = ""
            else:
                replace_none_with_empty_string_inplace(item)  # pyright: ignore[reportUnknownArgumentType]
    elif isinstance(obj, dict):
        for key, value in obj.items():
            if value is None:
                obj[key] = ""
            else:
                replace_none_with_empty_string_inplace(obj[key])  # pyright: ignore[reportUnknownArgumentType]
    elif isinstance(obj, IterMixin):
        for item in obj:
            if getattr(obj, item[0]) is None:
                setattr(obj, item[0], "")
            else:
                replace_none_with_empty_string_inplace(getattr(obj, item[0]))  # pyright: ignore[reportUnknownArgumentType]


def run_async_function(async_func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:  # noqa: ANN401 # pyright: ignore[reportUnknownParameterType]
    result: Any | None = None
    exception = None

    def run_in_thread() -> None:
        nonlocal result, exception
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            result = new_loop.run_until_complete(async_func(*args, **kwargs))  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType, reportArgumentType]
            new_loop.close()
        except Exception as e:
            exception = e

    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            if threading.current_thread() is threading.main_thread():
                loop_thread = threading.Thread(target=run_in_thread)
                loop_thread.start()
                loop_thread.join()
            else:
                result = asyncio.run(async_func(*args, **kwargs))  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType, reportArgumentType]
    except RuntimeError:
        result = asyncio.run(async_func(*args, **kwargs))  # pyright: ignore[reportUnknownVariableType, reportArgumentType]

    if exception:
        raise exception
    return result  # pyright: ignore[reportUnknownVariableType]
