import logging
from pathlib import Path
from typing import Any

from amt.schema.measure import MeasureBase
from amt.schema.requirement import RequirementBase
from amt.schema.system_card import AiActProfile
from amt.services.storage import StorageFactory

logger = logging.getLogger(__name__)


def get_requirements_and_measures(
    self , ai_act_profile: AiActProfile
) -> tuple[
    list[RequirementBase] ,
    list[MeasureBase] ,
]:
    # TODO: This now loads measures & requirements from the example system card independent of the project ID.
    # TODO: Refactor to call the task registry here (based on the ai_act_profile)
    # TODO: Refactor and merge both the InstrumentService and this TaskRegsitryService to make use of the TaskRegistry
    measure_path = Path('example_system_card/measures/measures.yaml')
    requirements_path = Path('example_system_card/requirements/requirements.yaml')
    measures: Any = StorageFactory.init(storage_type="file" ,
                                        location=measure_path.parent ,
                                        filename=measure_path.name).read()
    requirements: Any = StorageFactory.init(storage_type="file" ,
                                            location=requirements_path.parent ,
                                            filename=requirements_path.name).read()
    measure_card = [MeasureBase(**measure) for measure in measures]
    requirements_card = [RequirementBase(**requirement) for requirement in requirements]

    return requirements_card , measure_card
