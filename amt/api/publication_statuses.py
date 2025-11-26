from collections.abc import Callable

from fastapi import Request

from ..schema.localized_value_item import LocalizedValueItem
from .localizable import LocalizableEnum, get_localized_enum, get_localized_enums


class PublicationStatuses(LocalizableEnum):
    NONE = "NONE"
    STATE_1 = "STATE_1"
    STATE_2 = "STATE_2"
    PUBLISHED = "PUBLISHED"

    @classmethod
    def get_display_values(
        cls: type["PublicationStatuses"], _: Callable[[str], str]
    ) -> dict["PublicationStatuses", str]:
        return {
            cls.NONE: _("Not supplied"),
            cls.STATE_1: _("Supplied"),
            cls.STATE_2: _("Approved"),
            cls.PUBLISHED: _("Published"),
        }


def get_localized_publication_status(key: PublicationStatuses | None, request: Request) -> LocalizedValueItem | None:
    return get_localized_enum(key, request)


def get_localized_publication_statuses(
    request: Request,
) -> list[LocalizedValueItem | None]:
    return get_localized_enums(PublicationStatuses, request)
