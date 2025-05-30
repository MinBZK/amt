from enum import IntEnum, StrEnum

from amt.api.forms.measure import MeasureStatusOptions
from amt.api.lifecycles import Lifecycles


class Status(IntEnum):
    TODO = 1
    IN_PROGRESS = 2
    IN_REVIEW = 3
    DONE = 4
    NOT_IMPLEMENTED = 5


class TaskType(StrEnum):
    MEASURE = "measure"


status_mapper: dict[Status, MeasureStatusOptions] = {
    Status.TODO: MeasureStatusOptions.TODO,
    Status.IN_PROGRESS: MeasureStatusOptions.IN_PROGRESS,
    Status.IN_REVIEW: MeasureStatusOptions.IN_REVIEW,
    Status.DONE: MeasureStatusOptions.DONE,
    Status.NOT_IMPLEMENTED: MeasureStatusOptions.NOT_IMPLEMENTED,
}


def measure_state_to_status(state: str) -> Status:
    return next((k for k, v in status_mapper.items() if v.value == state), Status.TODO)


life_cycle_mapper: dict[Lifecycles, str] = {
    Lifecycles.ORGANIZATIONAL_RESPONSIBILITIES: "organisatieverantwoordelijkheden",
    Lifecycles.PROBLEM_ANALYSIS: "probleemanalyse",
    Lifecycles.DESIGN: "ontwerp",
    Lifecycles.DATA_EXPLORATION_AND_PREPARATION: "dataverkenning en datapreparatie",
    Lifecycles.DEVELOPMENT: "ontwikkelen",
    Lifecycles.VERIFICATION_AND_VALIDATION: "verificatie en validatie",
    Lifecycles.IMPLEMENTATION: "implementatie",
    Lifecycles.MONITORING_AND_MANAGEMENT: "monitoring en beheer",
    Lifecycles.PHASING_OUT: "uitfaseren",
}
