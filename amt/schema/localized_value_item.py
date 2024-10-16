from pydantic import BaseModel


class LocalizedValueItem(BaseModel):
    value: str
    display_value: str
