from pydantic import BaseModel, Field


class AlgoritmeregisterCredentials(BaseModel):
    username: str = Field()
    password: str = Field()
    token: str | None = Field(default=None)
