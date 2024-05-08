from pydantic import BaseModel


class Task(BaseModel):
    id: int
    title: str = "Jane Doe"
    description: str = ""
    status: str = ""
