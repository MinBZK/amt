from collections.abc import Generator, Iterator
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel as PydanticBaseModel


class IterMixin:
    def __iter__(self) -> Generator[tuple[str, Any], Any, Any]:
        yield from self.__dict__.items()


class BaseModel(PydanticBaseModel, IterMixin): ...


T = TypeVar("T")


class IterableProtocol(Protocol):
    def __iter__(self) -> Iterator[Any]: ...


class IterableMeta(type):
    def __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> type[Any]:
        def __iter__(self: object) -> Iterator[Any]:
            attrs = [attr for attr in dir(self) if not attr.startswith("__") and not callable(getattr(self, attr))]
            for attr in attrs:
                yield getattr(self, attr)

        namespace["__iter__"] = __iter__
        return super().__new__(mcs, name, bases, namespace)
