from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator


class ProjectBase(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    lifecycle: str = Field()


class ProjectNew(ProjectBase):
    instruments: list[str] | str = []
    type: str = Field(default=None)
    open_source: str = Field(default=None)
    publication_category: str = Field(default=None)
    systemic_risk: str = Field(default=None)
    transparency_obligations: str = Field(default=None)
    role: list[str] | str = []

    @field_validator("instruments", "role")
    def ensure_list(cls, v: list[str] | str) -> list[str]:
        return v if isinstance(v, list) else [v]
