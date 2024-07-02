from pydantic import BaseModel


class Owner(BaseModel):
    organization: str
    name: str
    email: str
    role: str


class InstrumentBase(BaseModel):
    urn: str


class Instrument(InstrumentBase):
    description: str
    name: str
    language: str
    owners: list[Owner]
    date: str
    url: str
