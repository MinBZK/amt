import logging
from enum import Enum

from fastapi import Request

from amt.core.internationalization import get_current_translation
from amt.schema.lifecycle import Lifecycle

logger = logging.getLogger(__name__)


class Lifecycles(Enum):
    ORGANIZATIONAL_RESPONSIBILITIES = "ORGANIZATIONAL_RESPONSIBILITIES"
    PROBLEM_ANALYSIS = "PROBLEM_ANALYSIS"
    DESIGN = "DESIGN"
    DATA_EXPLORATION_AND_PREPARATION = "DATA_EXPLORATION_AND_PREPARATION"
    DEVELOPMENT = "DEVELOPMENT"
    VERIFICATION_AND_VALIDATION = "VERIFICATION_AND_VALIDATION"
    IMPLEMENTATION = "IMPLEMENTATION"
    MONITORING_AND_MANAGEMENT = "MONITORING_AND_MANAGEMENT"
    PHASING_OUT = "PHASING_OUT"

    @property
    def index(self) -> int:
        return list(Lifecycles).index(self)


def get_lifecycle(key: Lifecycles | None, request: Request) -> Lifecycle | None:
    """
    Given the key and translation, returns the translated text.
    :param key: the key
    :param request: request to get the current language
    :return: a Lifecycle model with the correct translation
    """

    if key is None:
        return None

    translations = get_current_translation(request)
    _ = translations.gettext
    # translations are determined at runtime, which is why we use the dictionary below
    keys = {
        Lifecycles.ORGANIZATIONAL_RESPONSIBILITIES: _("Organizational Responsibilities"),
        Lifecycles.PROBLEM_ANALYSIS: _("Problem Analysis"),
        Lifecycles.DESIGN: _("Design"),
        Lifecycles.DATA_EXPLORATION_AND_PREPARATION: _("Data Exploration and Preparation"),
        Lifecycles.DEVELOPMENT: _("Development"),
        Lifecycles.VERIFICATION_AND_VALIDATION: _("Verification and Validation"),
        Lifecycles.IMPLEMENTATION: _("Implementation"),
        Lifecycles.MONITORING_AND_MANAGEMENT: _("Monitoring and Management"),
        Lifecycles.PHASING_OUT: _("Phasing Out"),
    }
    return Lifecycle(id=key.value, name=keys[key])


def get_lifecycles(request: Request) -> list[Lifecycle | None]:
    lifecycles: list[Lifecycle | None] = [get_lifecycle(lifecycle, request) for lifecycle in Lifecycles]
    return lifecycles
