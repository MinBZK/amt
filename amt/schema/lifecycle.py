from pydantic import BaseModel


class Lifecycle(BaseModel):
    id: str
    name: str
