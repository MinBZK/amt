from collections.abc import Callable

from fastapi import Request

from ..schema.localized_value_item import LocalizedValueItem
from .localizable import LocalizableEnum, get_localized_enum, get_localized_enums


class OrganizationFilterOptions(LocalizableEnum):
    ALL = "ALL"
    MY_ORGANIZATIONS = "MY_ORGANIZATIONS"

    @classmethod
    def get_display_values(
        cls: type["OrganizationFilterOptions"], _: Callable[[str], str]
    ) -> dict["OrganizationFilterOptions", str]:
        return {cls.ALL: _("All organizations"), cls.MY_ORGANIZATIONS: _("My organizations")}


def get_localized_organization_filter(
    key: OrganizationFilterOptions | None, request: Request
) -> LocalizedValueItem | None:
    return get_localized_enum(key, request)


def get_localized_organization_filters(request: Request) -> list[LocalizedValueItem | None]:
    return get_localized_enums(OrganizationFilterOptions, request)
