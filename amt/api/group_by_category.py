from collections.abc import Callable

from fastapi import Request

from ..schema.localized_value_item import LocalizedValueItem
from .localizable import LocalizableEnum, get_localized_enums


class GroupByCategories(LocalizableEnum):
    LIFECYCLE = "levenscyclus"

    @classmethod
    def get_display_values(cls: type["GroupByCategories"], _: Callable[[str], str]) -> dict["GroupByCategories", str]:
        return {
            cls.LIFECYCLE: _("Lifecycle"),
        }


def get_localized_group_by_categories(request: Request) -> list[LocalizedValueItem | None]:
    return get_localized_enums(GroupByCategories, request)
