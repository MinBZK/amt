from pydantic import Field

from amt.schema.shared import BaseModel


class RequirementBase(BaseModel):
    urn: str


class RequirementTask(RequirementBase):
    state: str
    version: str


class Requirement(RequirementBase):
    name: str
    description: str
    links: list[str] = Field(default=[])
