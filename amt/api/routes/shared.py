from collections.abc import Generator
from typing import Any

from starlette.requests import Request

from amt.api.lifecycles import Lifecycles, get_localized_lifecycle
from amt.api.organization_filter_options import OrganizationFilterOptions, get_localized_organization_filter
from amt.api.risk_group import RiskGroup, get_localized_risk_group
from amt.schema.localized_value_item import LocalizedValueItem
from amt.schema.webform import WebFormFieldImplementationType

type EditableType = Editable


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


class Editable:
    resource: str
    implementation_type: WebFormFieldImplementationType
    couples: set[EditableType]
    children: set[EditableType]
    # TODO future:
    #  conversions, we may need to convert in/out data
    #  combine with permissions?

    def __init__(
        self,
        resource: str,
        implementation_type: WebFormFieldImplementationType,
        couples: [list[EditableType]] = None,
        children: [list[EditableType]] = None,
    ) -> None:
        self.resource = resource
        self.implementation_type = implementation_type
        self.couples = set() if couples is None else couples
        self.children = set() if children is None else children

    def add_bidirectional_couple(self, target: EditableType) -> None:
        self.couples.add(target)
        target.couples.add(self)

    def add_child(self, target: EditableType) -> None:
        self.children.add(target)


class Editables:
    ALGORITHM_EDITABLE_NAME: Editable = Editable(
        resource="algorithm/{algorithm_id}/name", implementation_type=WebFormFieldImplementationType.TEXT
    )
    ALGORITHM_EDITABLE_SYSTEMCARD_NAME = Editable(
        resource="algorithm/{algorithm_id}/system_card/name", implementation_type=WebFormFieldImplementationType.TEXT
    )
    ALGORITHM_EDITABLE_NAME.add_bidirectional_couple(ALGORITHM_EDITABLE_SYSTEMCARD_NAME)

    ALGORITHM_EDITABLE_AUTHOR = Editable(
        resource="algorithm/{algorithm_id}/system_card/provenance/author",
        implementation_type=WebFormFieldImplementationType.TEXT,
    )
    ALGORITHM_EDITABLE_SYSTEMCARD_OWNERS = Editable(
        resource="algorithm/{algorithm_id}/system_card/owners[*]-disabled-for-now",
        implementation_type=WebFormFieldImplementationType.PARENT,
        children=(
            Editable(
                resource="algorithm/{algorithm_id}/system_card/owners[*]/organization",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
            Editable(
                resource="algorithm/{algorithm_id}/system_card/owners[*]/oin",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
        ),
    )

    ALGORITHM_EDITABLE_ORGANIZATION = Editable(
        resource="algorithm/{algorithm_id}/organization",
        implementation_type=WebFormFieldImplementationType.SELECT_MY_ORGANIZATIONS,
    )
    ALGORITHM_EDITABLE_DESCRIPTION = Editable(
        resource="algorithm/{algorithm_id}/system_card/description",
        implementation_type=WebFormFieldImplementationType.TEXTAREA,
    )
    ALGORITHM_EDITABLE_LIFECYCLE = Editable(
        resource="algorithm/{algorithm_id}/lifecycle",
        implementation_type=WebFormFieldImplementationType.SELECT_LIFECYCLE,
    )
    ALGORITHM_EDITABLE_SYSTEMCARD_STATUS = Editable(
        resource="algorithm/{algorithm_id}/system_card/status",
        implementation_type=WebFormFieldImplementationType.SELECT_LIFECYCLE,
    )
    ALGORITHM_EDITABLE_LIFECYCLE.add_bidirectional_couple(ALGORITHM_EDITABLE_SYSTEMCARD_STATUS)

    # TODO: rethink if this is a wise solution..
    def __iter__(self) -> Generator[tuple[str, Any], Any, Any]:
        yield from [
            getattr(self, attr) for attr in dir(self) if not attr.startswith("__") and not callable(getattr(self, attr))
        ]


editables = Editables()


def get_editables(context_variables: dict[str, str | int]) -> dict[str, Editable]:
    editables_resolved = []

    class SafeDict(dict):
        def __missing__(self, key: str) -> str:
            return "{" + key + "}"

    def resolve_editable(
        editable: Editable, context_variables: dict[str, str | int], include_targets: bool
    ) -> Editable:
        if include_targets:
            targets = [resolve_editable(target, context_variables, False) for target in editable.couples]
            return Editable(
                resource=editable.resource.format_map(SafeDict(context_variables)),
                implementation_type=editable.implementation_type,
                couples=targets,
            )
        else:
            return Editable(
                resource=editable.resource.format_map(SafeDict(context_variables)),
                implementation_type=editable.implementation_type,
            )

    for editable in editables:
        editables_resolved.append(resolve_editable(editable, context_variables, True))
    return {editable.resource: editable for editable in editables_resolved}
