from collections.abc import Callable

from fastapi import Request

from ..schema.localized_value_item import LocalizedValueItem
from .localizable import LocalizableEnum, get_localized_enum, get_localized_enums


class RiskGroup(LocalizableEnum):
    HOOG_RISICO_AI = "hoog-risico AI"
    GEEN_HOOG_RISICO_AI = "geen hoog-risico AI"
    VERBODEN_AI = "verboden AI"
    UITZONDERING_VAN_TOEPASSING = "uitzondering van toepassing"
    NIET_VAN_TOEPASSING = "niet van toepassing"

    @classmethod
    def get_display_values(cls: type["RiskGroup"], _: Callable[[str], str]) -> dict["RiskGroup", str]:
        return {
            cls.HOOG_RISICO_AI: _("hoog-risico AI"),
            cls.GEEN_HOOG_RISICO_AI: _("geen hoog-risico AI"),
            cls.VERBODEN_AI: _("verboden AI"),
            cls.UITZONDERING_VAN_TOEPASSING: _("uitzondering van toepassing"),
            cls.NIET_VAN_TOEPASSING: _("niet van toepassing"),
        }


def get_localized_risk_group(key: RiskGroup | None, request: Request) -> LocalizedValueItem | None:
    return get_localized_enum(key, request)


def get_localized_risk_groups(request: Request) -> list[LocalizedValueItem | None]:
    return get_localized_enums(RiskGroup, request)
