import logging
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

from amt.schema.measure import Measure, MeasureTask
from amt.schema.requirement import Requirement, RequirementTask
from amt.schema.system_card import AiActProfile
from amt.services.storage import StorageFactory

logger = logging.getLogger(__name__)


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


@lru_cache
def fetch_all_requirements() -> dict[str, Requirement]:
    """
    Fetch requirements with URN in urns.
    """
    mock_registry_path = Path("example_registry/requirements")
    requirements: dict[str, Requirement] = {}

    for requirement_path in mock_registry_path.glob("*.yaml"):
        requirement: Any = StorageFactory.init(
            storage_type="file", location=requirement_path.parent, filename=requirement_path.name
        ).read()
        requirements[requirement["urn"]] = Requirement(**requirement)

    return requirements


def fetch_requirements(urns: Sequence[str]) -> list[Requirement]:
    """
    Fetch requirements with URN in urns.
    """
    all_requirements = fetch_all_requirements()
    return [all_requirements[urn] for urn in urns if urn in all_requirements]


@lru_cache
def fetch_all_measures() -> dict[str, Measure]:
    """
    Fetch measures with URN in urns.
    """
    mock_registry_path = Path("example_registry/measures")
    measures: dict[str, Measure] = {}

    for measure_path in mock_registry_path.glob("*.yaml"):
        measure: Any = StorageFactory.init(
            storage_type="file", location=measure_path.parent, filename=measure_path.name
        ).read()
        measures[measure["urn"]] = Measure(**measure)

    return measures


def fetch_measures(urns: Sequence[str]) -> list[Measure]:
    """
    Fetch measures with URN in urns.
    """
    all_measures = fetch_all_measures()
    return [all_measures[urn] for urn in urns if urn in all_measures]
