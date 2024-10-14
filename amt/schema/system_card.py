from typing import Any

from pydantic import (
    BaseModel,
    Field,  # pyright: ignore [reportUnknownMemberType]
)

from amt.schema.ai_act_profile import AiActProfile
from amt.schema.assessment_card import AssessmentCard
from amt.schema.instrument import InstrumentBase
from amt.schema.measure import MeasureTask
from amt.schema.requirement import RequirementTask


class SystemCard(BaseModel):
    schema_version: str = Field(default="0.1a10")
    name: str = Field(default=None)
    ai_act_profile: AiActProfile = Field(default=None)
    provenance: dict[str, Any] = Field(default={})
    description: str = Field(default=None)
    labels: list[dict[str, Any]] = Field(default=[])
    status: str = Field(default=None)
    instruments: list[InstrumentBase] = Field(default=[])
    requirements: list[RequirementTask] = Field(default=[])
    measures: list[MeasureTask] = Field(default=[])
    assessments: list[AssessmentCard] = Field(default=[])
