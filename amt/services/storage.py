from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, TypedDict, Unpack

import yaml
import yaml_include
from yaml import dump

from amt.core.exceptions import AMTKeyError, AMTValueError


class WriterFactoryArguments(TypedDict):
    location: str | Path
    filename: str


class Storage(ABC):
    @abstractmethod
    def read(self) -> None:
        """This is an abstract method to write with the writer"""

    @abstractmethod
    def write(self, data: dict[str, Any]) -> None:
        """This is an abstract method to write with the writer"""

    @abstractmethod
    def close(self) -> None:
        """This is an abstract method to close the writer"""


class StorageFactory:
    @staticmethod
    def init(storage_type: str = "file", **kwargs: Unpack[WriterFactoryArguments]) -> Storage:
        match storage_type:
            case "file":
                if not all(k in kwargs for k in ("location", "filename")):
                    raise AMTKeyError("`location` | `filename`")
                return FileSystemStorageService(location=Path(kwargs["location"]), filename=str(kwargs["filename"]))
            case _:
                raise AMTValueError(storage_type)


class FileSystemStorageService(Storage):
    def __init__(self, location: Path = Path("./tests/data"), filename: str = "system_card.yaml") -> None:
        self.base_dir = location
        if not filename.endswith(".yaml"):
            raise AMTValueError(filename)
        self.filename = filename
        self.path = self.base_dir / self.filename

    def write(self, data: dict[str, Any]) -> None:
        if not Path(self.base_dir).exists():
            Path(self.base_dir).mkdir()
        with open(self.path, "w") as f:
            dump(data, f, default_flow_style=False, sort_keys=False)

    def read(self) -> Any:  # noqa
        # todo: this probably has to be moved to 'global scope'
        yaml.add_constructor("!include", yaml_include.Constructor(base_dir=self.base_dir))
        with open(self.path) as f:
            return yaml.full_load(f)

    def close(self) -> None:
        """
        This method is empty because with the `with` statement in the writer, Python will already close the writer
        after usage.
        """
