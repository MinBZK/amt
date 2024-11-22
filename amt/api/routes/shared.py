from starlette.requests import Request

from amt.api.lifecycles import Lifecycles, get_localized_lifecycle
from amt.api.organization_filter_options import OrganizationFilterOptions, get_localized_organization_filter
from amt.api.risk_group import RiskGroup, get_localized_risk_group
from amt.schema.localized_value_item import LocalizedValueItem


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
