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


mock_requirements_registry = {
    "urn:nl:ak:ver:aia-7": {
        "name": "Automatische logregistratie voor hoog-risico AI",
        "description": "Algoritmes en AI-systemen zijn dusdanig technisch vormgegeven dat \
                gebeurtenissen gedurende hun levenscyclus automatisch worden geregistreerd (“logs”).",
        "urn": "urn:nl:ak:ver:aia-7",
    },
    "urn:nl:ak:ver:awb-01": {
        "name": "Relevante feiten en belangen zijn bekend",
        "description": "De ontwikkeling en het gebruik van algoritmes en AI-systemen komt zorgvuldig tot stand.",
        "urn": "urn:nl:ak:ver:awb-01",
    },
}

mock_measures_registry = {
    "urn:nl:ak:mtr:pin:01": {
        "name": "Bespreek de vereiste met aanbieder of opdrachtnemer.",
        "description": "Ga met een aanbieder en/of met opdrachtnemers in gesprek over in hoeverre \
                deze invulling heeft gegeven of gaat geven aan de vereiste. Op basis van nieuwe of \
                gewijzigde wet- en regelgeving is het denkbaar dat een aanbieder van algoritmes of \
                AI-systemen nog niet of niet meer voldoet aan deze vereiste. Indien van toepassing,\
                laat de aanbieder inzichtelijk maken welke stappen deze gaat zetten om hieraan te \
                gaan voldoen. Dit is ook relevant bij reeds afgesloten contracten.",
        "urn": "urn:nl:ak:mtr:pin:01",
    }
}


def fetch_requirements(urns: Sequence[str]) -> list[Requirement]:
    return [Requirement(**mock_requirements_registry[urn]) for urn in urns]


def fetch_measures(urns: Sequence[str]) -> list[Measure]:
    return [Measure(**mock_measures_registry[urn]) for urn in urns]
