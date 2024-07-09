from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator


class ProjectBase(BaseModel):
    name: str = Field(min_length=3, max_length=255)


class ProjectNew(ProjectBase):
    instruments: list[str] | str = []

    @field_validator("instruments")
    def ensure_list(cls, v: list[str] | str) -> list[str]:
        return v if isinstance(v, list) else [v]
