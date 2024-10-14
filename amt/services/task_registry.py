import logging
from collections.abc import Sequence
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
    # TODO: This now loads measures & requirements from the example system card independent of the project ID.
    # TODO: Refactor to call the task registry api here (based on the ai_act_profile) NOT the system card which is very
    # artificial and has extra information like status and value.
    # TODO: Refactor and merge both the InstrumentService and this TaskRegsitryService to make use of the TaskRegistry
    measure_path = Path("example_system_card/measures/measures.yaml")
    requirements_path = Path("example_system_card/requirements/requirements.yaml")
    measures: Any = StorageFactory.init(
        storage_type="file", location=measure_path.parent, filename=measure_path.name
    ).read()
    requirements: Any = StorageFactory.init(
        storage_type="file", location=requirements_path.parent, filename=requirements_path.name
    ).read()
    measure_card = [MeasureTask(**measure) for measure in measures]
    requirements_card = [RequirementTask(**requirement) for requirement in requirements]

    # TODO: After calling the Task Registry API this should return a MeasureBase and RequirementBase
    return requirements_card, measure_card


def fetch_requirements(urns: Sequence[str]) -> list[Requirement]:
    """
    Fetch requirements with URN in urns.
    """
    # TODO: make this cacheable (not use a sequence/list as input argument)
    mock_registry_path = Path("example_registry/requirements")
    requirements: list[Requirement] = []

    required_urns: set[str] = set(urns)
    for requirement_path in mock_registry_path.glob("*.yaml"):
        requirement: Any = StorageFactory.init(
            storage_type="file", location=requirement_path.parent, filename=requirement_path.name
        ).read()
        if requirement["urn"] in required_urns:
            requirements.append(Requirement(**requirement))

    return requirements


def fetch_measures(urns: Sequence[str]) -> list[Measure]:
    """
    Fetch measures with URN in urns.
    """
    mock_registry_path = Path("example_registry/measures")
    measures: list[Measure] = []

    required_urns: set[str] = set(urns)
    for measure_path in mock_registry_path.glob("*.yaml"):
        measure: Any = StorageFactory.init(
            storage_type="file", location=measure_path.parent, filename=measure_path.name
        ).read()
        if measure["urn"] in required_urns:
            measures.append(Measure(**measure))

    return measures
