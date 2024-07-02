from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, TypedDict

from yaml import dump


class WriterFactoryArguments(TypedDict):
    location: str | Path
    filename: str


class Writer(ABC):
    @abstractmethod
    def write(self, data: dict[str, Any]) -> None:
        """This is an abstract method to write with the writer"""

    @abstractmethod
    def close(self) -> None:
        """This is an abstract method to close the writer"""


class WriterFactory:
    @staticmethod
    def get_writer(writer_type: str = "file", **kwargs: Any) -> Writer:  # noqa: ANN401
        match writer_type:
            case "file":
                if not all(k in kwargs for k in ("location", "filename")):
                    raise KeyError("The `location` or `filename` variables are not provided as input for get_writer()")
                return FileSystemWriteService(location=kwargs["location"], filename=kwargs["filename"])
            case _:
                raise ValueError(f"Unknown writer type: {writer_type}")


class FileSystemWriteService(Writer):
    def __init__(self, location: str | Path = "./tests/data", filename: str = "system_card.yaml") -> None:
        self.location = location
        if not filename.endswith(".yaml"):
            raise ValueError(f"Filename {filename} must end with .yaml instead of .{filename.split('.')[-1]}")
        self.filename = filename

    def write(self, data: dict[str, Any]) -> None:
        if not Path(self.location).exists():
            Path(self.location).mkdir()
        with open(Path(self.location) / self.filename, "w") as f:
            dump(data, f, default_flow_style=False, sort_keys=False)

    def close(self) -> None:
        """
        This method is empty because with the `with` statement in the writer, Python will already close the writer
        after usage.
        """
