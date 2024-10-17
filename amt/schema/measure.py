from pydantic import BaseModel, Field


class MeasureBase(BaseModel):
    urn: str


class MeasureTask(MeasureBase):
    state: str
    version: str
    value: str


class Measure(MeasureBase):
    name: str
    description: str
    links: list[str] = Field(default=[])
    url: str


class ExtendedMeasureTask(MeasureTask):
    name: str
    description: str
