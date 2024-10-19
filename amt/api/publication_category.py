from collections.abc import Callable

from fastapi import Request

from ..schema.localized_value_item import LocalizedValueItem
from .localizable import LocalizableEnum, get_localized_enum, get_localized_enums


class PublicationCategories(LocalizableEnum):
    IMPACTVOL_ALGORITME = "impactvol algoritme"
    NIET_IMPACTVOL_ALGORITME = "niet-impactvol algoritme"
    HOOG_RISICO_AI = "hoog-risico AI"
    GEEN_HOOG_RISICO_AI = "geen hoog-risico AI"
    VERBODEN_AI = "verboden AI"
    UITZONDERING_VAN_TOEPASSING = "uitzondering van toepassing"

    @classmethod
    def get_display_values(
        cls: type["PublicationCategories"], _: Callable[[str], str]
    ) -> dict["PublicationCategories", str]:
        return {
            cls.IMPACTVOL_ALGORITME: _("Impactful algorithm"),
            cls.NIET_IMPACTVOL_ALGORITME: _("Non-impactful algorithm"),
            cls.HOOG_RISICO_AI: _("High-risk AI"),
            cls.GEEN_HOOG_RISICO_AI: _("No high-risk AI"),
            cls.VERBODEN_AI: _("Forbidden AI"),
            cls.UITZONDERING_VAN_TOEPASSING: _("Exception of application"),
        }


def get_localized_publication_category(
    key: PublicationCategories | None, request: Request
) -> LocalizedValueItem | None:
    return get_localized_enum(key, request)


def get_localized_publication_categories(request: Request) -> list[LocalizedValueItem | None]:
    return get_localized_enums(PublicationCategories, request)
