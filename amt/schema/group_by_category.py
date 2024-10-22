from pydantic import BaseModel


class GroupByCategory(BaseModel):
    id: str
    name: str
