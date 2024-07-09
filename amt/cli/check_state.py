import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
import yaml

from amt.schema.assessment_card import AssessmentCard
from amt.schema.instrument import Instrument, InstrumentTask
from amt.schema.system_card import SystemCard
from amt.services.instruments import InstrumentsService
from amt.services.storage import StorageFactory

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
    ["Ontwerp", "Monitoren"] will return 1
    ["Monitoren", "Ontwerp"] will return 1
    """

    for idx, lifecycle in enumerate(all_lifecycles):
        if lifecycle in lifecycles:
            return idx
    return 0


def get_system_card(path: Path) -> SystemCard:
    system_card: Any = StorageFactory.init(storage_type="file", location=path.parent, filename=path.name).read()
    return SystemCard(**system_card)


def get_requested_instruments(all_instruments: list[Instrument], urns: list[str]) -> dict[str, Instrument]:
    return {instrument.urn: instrument for instrument in all_instruments if instrument.urn in urns}


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
    next_tasks_per_instruments: list[dict[str, Any]] = []
    for urn, instrument in instruments.items():
        instrument_result_from_system_card = get_instrument_result_from_system_card(urn, system_card)
        next_tasks_per_instruments.append(get_next_tasks_per_instrument(instrument, instrument_result_from_system_card))
    next_tasks_per_instruments = sorted(next_tasks_per_instruments, key=lambda i: i["last_modified_date"], reverse=True)
    return next_tasks_per_instruments


@click.command()
@click.argument("urns", nargs=-1)
@click.argument("system_card_path", type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path))
def get_tasks_by_priority(urns: list[str], system_card_path: Path) -> None:
    try:
        system_card = get_system_card(system_card_path)
        instruments_service = InstrumentsService()
        all_instruments = instruments_service.fetch_instruments()
        instruments = get_requested_instruments(all_instruments, urns)
        next_tasks = get_all_next_tasks(instruments, system_card)

        for idx, lifecycle in enumerate(all_lifecycles):
            click.echo("=" * 40)
            click.echo(lifecycle)
            click.echo("=" * 40)
            for next_tasks_per_instrument in next_tasks:
                for task in next_tasks_per_instrument["tasks_per_lifecycle"][idx]:
                    click.echo(task.urn)
    except yaml.YAMLError as error:
        click.echo(f"Sorry, an error occurred; yaml could not be parsed: {error}", err=True)
        sys.exit(1)
    except Exception as error:
        click.echo(f"Sorry, an error occurred. {error}", err=True)
        sys.exit(1)
    sys.exit(0)
