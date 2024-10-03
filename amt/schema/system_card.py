from pydantic import (
    BaseModel,
    Field,  # pyright: ignore [reportUnknownMemberType]
)

from amt.schema.ai_act_profile import AiActProfile
from amt.schema.assessment_card import AssessmentCard
from amt.schema.instrument import InstrumentBase


class SystemCard(BaseModel):
    schema_version: str = Field(default="0.1a10")
    name: str = Field(default=None)
    ai_act_profile: AiActProfile = Field(default=None)
    provenance: dict = Field(default={})
    description: str = Field(default=None)
    labels: list = Field(default=[])
    status: str = Field(default=None)
    instruments: list[InstrumentBase] = Field(default=[])
    assessments: list[AssessmentCard] = Field(default=[])
