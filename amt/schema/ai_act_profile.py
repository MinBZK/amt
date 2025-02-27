from pydantic import Field

from amt.schema.shared import BaseModel


class AiActProfile(BaseModel):
    type: str | None = Field(default=None)
    open_source: str | None = Field(default=None)
    risk_group: str | None = Field(default=None)
    conformity_assessment_body: str | None = Field(default=None)
    systemic_risk: str | None = Field(default=None)
    transparency_obligations: str | None = Field(default=None)
    role: list[str] | str | None = Field(default=None)
