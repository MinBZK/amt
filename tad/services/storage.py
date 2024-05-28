from abc import ABC, abstractmethod
from pathlib import Path

from yaml import dump


class WriteService(ABC):
    def __init__(self, location: str, filename: str) -> None:
        self.location = location
        if not filename.endswith(".yaml"):
            raise ValueError(f"Filename {filename} must end with .yaml instead of .{filename.split('.')[-1]}")
        self.filename = filename

    @abstractmethod
    def write(self, data: dict) -> None:
        pass


class FileSystemWriteService(WriteService):
    def write(self, data):
        with open(Path(self.location) / self.filename, "w") as f:
            dump(data, f, default_flow_style=False, sort_keys=False)


class GitWriteService(WriteService):
    def write(self, data):
        raise NotImplementedError


class S3WriteService(WriteService):
    def write(self):
        raise NotImplementedError
