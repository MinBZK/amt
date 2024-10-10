from pydantic import BaseModel


class RequirementBase(BaseModel):
    urn: str
    state: str
    version: str
