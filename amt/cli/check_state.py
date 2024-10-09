import logging
import sys
from pathlib import Path
from typing import Any

import click
import yaml

from amt.schema.instrument import Instrument
from amt.schema.system_card import SystemCard
from amt.services.instruments import InstrumentsService
from amt.services.instruments_state import all_lifecycles, get_all_next_tasks
from amt.services.storage import StorageFactory

logger = logging.getLogger(__name__)


def get_system_card(path: Path) -> SystemCard:
    system_card: Any = StorageFactory.init(storage_type="file", location=path.parent, filename=path.name).read()
    return SystemCard(**system_card)


def get_requested_instruments(all_instruments: list[Instrument], urns: list[str]) -> dict[str, Instrument]:
    return {instrument.urn: instrument for instrument in all_instruments if instrument.urn in urns}


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
