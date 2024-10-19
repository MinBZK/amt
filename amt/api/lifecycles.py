from collections.abc import Callable

from fastapi import Request

from ..schema.localized_value_item import LocalizedValueItem
from .localizable import LocalizableEnum, get_localized_enum, get_localized_enums


class Lifecycles(LocalizableEnum):
    ORGANIZATIONAL_RESPONSIBILITIES = "ORGANIZATIONAL_RESPONSIBILITIES"
    PROBLEM_ANALYSIS = "PROBLEM_ANALYSIS"
    DESIGN = "DESIGN"
    DATA_EXPLORATION_AND_PREPARATION = "DATA_EXPLORATION_AND_PREPARATION"
    DEVELOPMENT = "DEVELOPMENT"
    VERIFICATION_AND_VALIDATION = "VERIFICATION_AND_VALIDATION"
    IMPLEMENTATION = "IMPLEMENTATION"
    MONITORING_AND_MANAGEMENT = "MONITORING_AND_MANAGEMENT"
    PHASING_OUT = "PHASING_OUT"

    @classmethod
    def get_display_values(cls: type["Lifecycles"], _: Callable[[str], str]) -> dict["Lifecycles", str]:
        return {
            cls.ORGANIZATIONAL_RESPONSIBILITIES: _("Organizational Responsibilities"),
            cls.PROBLEM_ANALYSIS: _("Problem Analysis"),
            cls.DESIGN: _("Design"),
            cls.DATA_EXPLORATION_AND_PREPARATION: _("Data Exploration and Preparation"),
            cls.DEVELOPMENT: _("Development"),
            cls.VERIFICATION_AND_VALIDATION: _("Verification and Validation"),
            cls.IMPLEMENTATION: _("Implementation"),
            cls.MONITORING_AND_MANAGEMENT: _("Monitoring and Management"),
            cls.PHASING_OUT: _("Phasing Out"),
        }


def get_localized_lifecycle(key: Lifecycles | None, request: Request) -> LocalizedValueItem | None:
    return get_localized_enum(key, request)


def get_localized_lifecycles(request: Request) -> list[LocalizedValueItem | None]:
    return get_localized_enums(Lifecycles, request)
