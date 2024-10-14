from pydantic import BaseModel


class MeasureBase(BaseModel):
    urn: str


class MeasureTask(MeasureBase):
    state: str
    version: str
    value: str


class Measure(MeasureBase):
    name: str
    description: str
