import logging

from amt.schema.measure import MeasureBase
from amt.schema.requirement import RequirementBase
from amt.schema.system_card import AiActProfile

logger = logging.getLogger(__name__)


class TaskRegistryService:
    def __init__(self) -> None:
        pass

    def get_requirements_and_measures(
        self, ai_act_profile: AiActProfile
    ) -> tuple[
        list[RequirementBase],
        list[MeasureBase],
    ]:
        raise NotImplementedError
