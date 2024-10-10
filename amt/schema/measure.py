from pydantic import BaseModel


class MeasureBase(BaseModel):
    urn: str
    state: str
    version: str
    value: str
