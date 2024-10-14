from pydantic import BaseModel, Field


class RequirementBase(BaseModel):
    urn: str


class RequirementTask(RequirementBase):
    state: str
    version: str


class Requirement(RequirementBase):
    name: str
    description: str
    links: list[str] = Field(default=[])
