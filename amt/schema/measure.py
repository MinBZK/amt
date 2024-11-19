from pydantic import Field

from amt.schema.shared import BaseModel


class MeasureBase(BaseModel):
    urn: str


class MeasureTask(MeasureBase):
    state: str = Field(default="")
    value: str = Field(default="")
    version: str


class Measure(MeasureBase):
    name: str
    schema_version: str
    description: str
    links: list[str] = Field(default=[])
    url: str


class ExtendedMeasureTask(MeasureTask):
    name: str
    description: str
