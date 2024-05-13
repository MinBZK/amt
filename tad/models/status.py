from pydantic import BaseModel


class Status(BaseModel):
    id: int
    name: str
    sort_order: float
