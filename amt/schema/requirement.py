from pydantic import BaseModel


class RequirementBase(BaseModel):
    urn: str


class RequirementTask(RequirementBase):
    state: str
    version: str


class Requirement(RequirementBase):
    name: str
    description: str
