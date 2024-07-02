from pathlib import Path
from typing import TypeVar

from pydantic import field_validator
from sqlmodel import Field, SQLModel  # pyright: ignore [reportUnknownVariableType]

T = TypeVar("T", bound="Project")


class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, min_items=3)
    model_card: str | None = Field(description="Model card storage location", default=None)

    @field_validator("model_card")
    @classmethod
    def validate_model_card(cls: type[T], model_card: str) -> str:
        if not Path(model_card).is_file():
            raise ValueError("Model card must be a file")

        return model_card
