from enum import Enum
from typing import Any

from pydantic import BaseModel
from starlette.requests import Request

from amt.api.lifecycles import Lifecycles, get_localized_lifecycle
from amt.api.localizable import LocalizableEnum
from amt.api.organization_filter_options import OrganizationFilterOptions, get_localized_organization_filter
from amt.api.risk_group import RiskGroup, get_localized_risk_group
from amt.schema.localized_value_item import LocalizedValueItem
from amt.schema.shared import IterMixin


def get_filters_and_sort_by(
    request: Request,
) -> tuple[dict[str, str], list[str], dict[str, LocalizedValueItem], dict[str, str]]:
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
    filters: dict[str, str] = {k: v for k, v in (active_filters | add_filters).items() if k not in drop_filters}
    localized_filters: dict[str, LocalizedValueItem] = {
        k: get_localized_value(k, v, request) for k, v in filters.items()
    }
    sort_by: dict[str, str] = {
        k.removeprefix("sort-by-"): v for k, v in request.query_params.items() if k.startswith("sort-by-") and v != ""
    }
    return filters, drop_filters, localized_filters, sort_by


def get_localized_value(key: str, value: str, request: Request) -> LocalizedValueItem:
    match key:
        case "lifecycle":
            localized = get_localized_lifecycle(Lifecycles(value), request)
        case "risk-group":
            localized = get_localized_risk_group(RiskGroup[value], request)
        case "organization-type":
            localized = get_localized_organization_filter(OrganizationFilterOptions(value), request)
        case _:
            localized = None

    if localized:
        return localized

    return LocalizedValueItem(value=value, display_value="Unknown filter option")


def get_nested(obj: Any, attr_path: str) -> Any:  # noqa: ANN401
    attrs = attr_path.lstrip("/").split("/") if "/" in attr_path else attr_path.lstrip(".").split(".")
    for attr in attrs:
        if hasattr(obj, attr):
            obj = getattr(obj, attr)
        elif isinstance(obj, dict) and attr in obj:
            obj = obj[attr]
        else:
            obj = None
            break
    return obj


def nested_value(obj: Any, attr_path: str) -> Any:  # noqa: ANN401
    obj = get_nested(obj, attr_path)
    if isinstance(obj, Enum):
        return obj.value
    return obj


def is_nested_enum(obj: Any, attr_path: str) -> bool:  # noqa: ANN401
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
            if item is None and isinstance(item, str):
                obj[i] = ""
            elif isinstance(item, list | dict | IterMixin):
                replace_none_with_empty_string_inplace(item)  # pyright: ignore[reportUnknownArgumentType]

    elif isinstance(obj, dict):
        for key, value in obj.items():
            if value is None and isinstance(value, str):
                obj[key] = ""
            elif isinstance(value, (list, dict, IterMixin)):  # noqa: UP038
                replace_none_with_empty_string_inplace(value)  # pyright: ignore[reportUnknownArgumentType]

    elif isinstance(obj, IterMixin):
        for item in obj:
            if isinstance(item, tuple) and item[1] is None:
                setattr(obj, item[0], "")
            if isinstance(item, list | dict | IterMixin):
                replace_none_with_empty_string_inplace(item)  # pyright: ignore[reportUnknownArgumentType]
