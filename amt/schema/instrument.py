from pydantic import BaseModel, Field


class Owner(BaseModel):
    organization: str
    name: str
    email: str
    role: str


class InstrumentTask(BaseModel):
    question: str
    urn: str
    type: list[str] = Field(default=[])
    lifecycle: list[str]


class InstrumentBase(BaseModel):
    urn: str


class Instrument(InstrumentBase):
    description: str
    name: str
    language: str
    owners: list[Owner]
    date: str
    url: str
    tasks: list[InstrumentTask] = Field(default=[])
