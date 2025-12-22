from pydantic import BaseModel, Field


class OrganisationOption(BaseModel):
    value: str
    label: str


class AlgoritmeregisterCredentials(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    organization_id: str | None = Field(default=None)
    token: str | None = Field(default=None)
    organisations: list[OrganisationOption] = Field(default_factory=list)
