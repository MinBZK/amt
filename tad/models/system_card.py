from pydantic import BaseModel
from pydantic import Field as PydanticField  # type: ignore


class SystemCard(BaseModel):
    title: str = PydanticField(None, alias="title", strict=False)
