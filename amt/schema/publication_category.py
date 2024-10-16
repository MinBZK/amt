from pydantic import BaseModel


class PublicationCategory(BaseModel):
    id: str
    name: str
