from collections.abc import Generator
from typing import Any

from pydantic import BaseModel as PydanticBaseModel


class IterMixin:
    def __iter__(self) -> Generator[tuple[str, Any], Any, Any]:
        yield from self.__dict__.items()


class BaseModel(PydanticBaseModel, IterMixin): ...
