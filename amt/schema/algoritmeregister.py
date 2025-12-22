from pydantic import BaseModel, Field


class AlgoritmeregisterCredentials(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    organization_id: str = Field(min_length=1)
    token: str | None = Field(default=None)
