import logging
from collections import defaultdict
from datetime import datetime , timezone
from typing import Any

from amt.schema.assessment_card import AssessmentCard
from amt.schema.instrument import Instrument, InstrumentTask
from amt.schema.system_card import SystemCard
from amt.services.instruments import InstrumentsService

logger = logging.getLogger(__name__)

all_lifecycles = (
    "Geen",
    "Probleemanalyse",
    "Ontwerp",
    "Monitoren",
    "Beheer",
    "Ontwikkelen",
    "Dataverkenning en -preparatie",
    "Verificatie",
    "Validatie",
    "Implementatie",
)

def get_first_lifecycle_idx(lifecycles: list[str]) -> int | None:
    """
    Return the index of the first lifecycle according to the
    above order given a list of lifecycles.

    Example:
    ["Ontwerp", "Monitoren"] will return 2
    ["Monitoren", "Ontwerp"] will return 2
    """

    for idx, lifecycle in enumerate(all_lifecycles):
        if lifecycle in lifecycles:
            return idx
    return 0


def get_instrument_result_from_system_card(urn: str, system_card: SystemCard) -> AssessmentCard | None:
    """
    Returns the results of the given instrument if it is found in the system card, otherwise None.
    :param urn: the urn of the instrument
    :param system_card: the data of the systemcard
    :return: the results of the instrument or None if it is not found
    """
    # TODO: Find out if this is "find fast" or the whole list is iterated.
    # TODO: Now we explicitly code assessments, because these are the only instruments that exists.
    #       How are we going to process non-assessment-like instruments?
    if system_card.assessments:
        return next((assessment for assessment in system_card.assessments if assessment.urn == urn), None)
    return None


def get_task_timestamp_from_assessment_card(task_urn: str, assessment_card: AssessmentCard) -> datetime | None:
    for content in assessment_card.contents:
        if content.urn == task_urn and content.timestamp:
            return content.timestamp
    return None


def get_next_tasks_per_instrument(instrument: Instrument, assessment_card: AssessmentCard | None) -> dict[str, Any]:
    return_value: dict[str, Any] = {
        "instrument_urn": instrument.urn,
        "last_modified_date": datetime(1970, 1, 1, tzinfo=timezone.utc),  # noqa UP017
        "tasks_per_lifecycle": defaultdict(list[InstrumentTask]),
    }

    for instrument_task in instrument.tasks:
        timestamp = (
            get_task_timestamp_from_assessment_card(instrument_task.urn, assessment_card) if assessment_card else None
        )

        if timestamp and timestamp >= return_value["last_modified_date"]:
            return_value["last_modified_date"] = timestamp
        else:
            lifecycle_order = get_first_lifecycle_idx(instrument_task.lifecycle)
            return_value["tasks_per_lifecycle"][lifecycle_order].append(instrument_task)
    return return_value


def get_all_next_tasks(instruments: dict[str, Instrument], system_card: SystemCard) -> list[dict[str, Any]]:
    # Rewrite to use the instruments from the systemcard
    next_tasks_per_instruments: list[dict[str, Any]] = []
    for urn, instrument in instruments.items():
        instrument_result_from_system_card = get_instrument_result_from_system_card(urn, system_card)
        next_tasks_per_instruments.append(get_next_tasks_per_instrument(instrument, instrument_result_from_system_card))
    next_tasks_per_instruments = sorted(next_tasks_per_instruments, key=lambda i: i["last_modified_date"], reverse=True)
    return next_tasks_per_instruments


class InstrumentStateService:
    def __init__(self, system_card : SystemCard) -> None:
        self.system_card = system_card
        self.instrument_state = {}

    def get_state_per_instrument(self) -> dict[str, int]:
        urns = [instrument.urn for instrument in self.system_card.instruments]
        instruments = InstrumentsService().fetch_instruments(urns)
        # refactor this data structure in 3 lines below (also change in get_all_next_tasks + check_state.py)
        instruments_dict = {}
        for instrument in instruments:
            instruments_dict[instrument.urn] = instrument
        next_tasks = get_all_next_tasks(instruments_dict, self.system_card)

        instrument_state = {}
        for tasks_per_instrument in next_tasks:
            instrument_state[tasks_per_instrument["instrument_urn"]] = 0
            for idx , lifecycle in enumerate(all_lifecycles):
                for task in tasks_per_instrument["tasks_per_lifecycle"][idx]:
                    if task is not None:
                        instrument_state[tasks_per_instrument["instrument_urn"]] += 1
                        break # If a task has been found which is not completed yet break out of the loop

        for instrument in instrument_state:
            if instrument_state[instrument] > 0:
                instrument_state[instrument] = 1

        # Returns dictionary with instrument urns with value 0 or 1, if 1 then the instrument is not completed yet
        # Otherwise the instrument is completed as there are not any tasks left.
        self.instrument_state = instrument_state
        return instrument_state


    def get_amount_completed_instruments(self) -> int:
        count_completed = 0
        for instrument_urn, status in self.instrument_state.items():
            if status == 0:
                count_completed += 1
        return count_completed

    def get_amount_total_instruments(self) -> int:
        return len(self.instrument_state.keys())