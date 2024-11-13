import logging

from amt.schema.measure import MeasureTask
from amt.schema.requirement import RequirementTask
from amt.schema.system_card import AiActProfile

logger = logging.getLogger(__name__)


def get_requirements(ai_act_profile: AiActProfile) -> list[RequirementTask]:
    requirements: list[RequirementTask] = []

    return requirements


def get_requirements_and_measures(
    ai_act_profile: AiActProfile,
) -> tuple[
    list[RequirementTask],
    list[MeasureTask],
]:
    # TODO (Robbert): the body of this method will be added later (another ticket)
    measure_card: list[MeasureTask] = []
    requirements_card: list[RequirementTask] = []

    return requirements_card, measure_card
