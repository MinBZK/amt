from typing import Any

from pydantic import Field

from amt.schema.ai_act_profile import AiActProfile
from amt.schema.assessment_card import AssessmentCard
from amt.schema.instrument import InstrumentBase
from amt.schema.measure import MeasureTask
from amt.schema.model_card import ModelCardSchema
from amt.schema.requirement import RequirementTask
from amt.schema.shared import BaseModel


class Reference(BaseModel):
    name: str = Field(default=None)
    link: str = Field(default=None)


# TODO: consider reusing classes, Owner is now also defined for Models
class Owner(BaseModel):
    organization: str = Field(default=None)
    oin: str | None = Field(default=None)

    def __init__(self, organization: str, oin: str | None = None, **data) -> None:  # pyright: ignore # noqa
        super().__init__(**data)
        self.organization = organization


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
    references: list[Reference] = Field(default=[])
    models: list[ModelCardSchema] = Field(default=[])
    owners: list[Owner] = Field(default=[])
