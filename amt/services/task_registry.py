import logging

from amt.schema.measure import MeasureTask
from amt.schema.requirement import Requirement, RequirementTask
from amt.schema.system_card import AiActProfile
from amt.services.measures import create_measures_service
from amt.services.requirements import create_requirements_service

logger = logging.getLogger(__name__)


def is_requirement_applicable(requirement: Requirement, ai_act_profile: AiActProfile) -> bool:
    """
    Determine if a specific requirement is applicable to a given AI Act profile.

    Evaluation Criteria:
    - Always applicable requirements automatically return True.
    - For the 'role' attribute, handles compound values like
      "gebruiksverantwoordelijke + aanbieder".
    - For the 'systemic_risk' attribute, handles the old name 'publication_category'.
    - A requirement is applicable if all specified attributes match or have no
      specific restrictions.
    """
    if requirement.always_applicable == 1:
        return True

    # We can assume the ai_act_profile field always contains exactly 1 element.
    requirement_profile = requirement.ai_act_profile[0]
    comparison_attrs = (
        "type",
        "risk_group",
        "role",
        "open_source",
        "systemic_risk",
        "transparency_obligations",
        "conformity_assessment_body",
    )

    for attr in comparison_attrs:
        requirement_attr_values = getattr(requirement_profile, attr, [])

        if not requirement_attr_values:
            continue

        input_value = _parse_attribute_values(attr, ai_act_profile)

        if not input_value & {attr_value.value for attr_value in requirement_attr_values}:
            return False

    return True


async def get_requirements_and_measures(
    ai_act_profile: AiActProfile,
) -> tuple[list[RequirementTask], list[MeasureTask]]:
    requirements_service = create_requirements_service()
    measure_service = create_measures_service()
    all_requirements = await requirements_service.fetch_requirements()

    applicable_requirements: list[RequirementTask] = []
    applicable_measures: list[MeasureTask] = []
    measure_urns: set[str] = set()

    for requirement in all_requirements:
        if is_requirement_applicable(requirement, ai_act_profile):
            applicable_requirements.append(RequirementTask(urn=requirement.urn, version=requirement.schema_version))

            for measure_urn in requirement.links:
                if measure_urn not in measure_urns:
                    measure = await measure_service.fetch_measures(measure_urn)
                    applicable_measures.append(
                        MeasureTask(urn=measure_urn, state="to do", version=measure[0].schema_version)
                    )
                    measure_urns.add(measure_urn)

    return applicable_requirements, applicable_measures


def _parse_attribute_values(attr: str, ai_act_profile: AiActProfile) -> set[str]:
    """
    Helper function needed in `is_requirement_applicable`, handling special case for 'role'
    and 'publication_category'.
    """
    if attr == "role":
        return {s.strip() for s in getattr(ai_act_profile, attr, "").split("+")}
    if attr == "risk_group":
        return {getattr(ai_act_profile, "risk_group", "")}

    return {getattr(ai_act_profile, attr, "")}
