from pydantic import BaseModel


class Task(BaseModel):
    id: int
    title: str
    description: str
    sort_order: float
    status_id: int
    user_id: int | None = None
