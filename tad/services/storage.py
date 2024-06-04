from abc import ABC, abstractmethod
from pathlib import Path

from yaml import dump


class WriterFactory(ABC):
    @staticmethod
    def get_writer(writer_type: str = "file", **kwargs):
        match writer_type:
            case "file":
                return FileSystemWriteService(location=kwargs["location"], filename=kwargs["filename"])
            case "s3":
                return S3WriteService(kwargs)
            case "git":
                return GitWriteService(kwargs)
            case _:
                raise ValueError(f"Unknown writer type: {writer_type}")

    @abstractmethod
    def write(self, data: dict) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class FileSystemWriteService(WriterFactory):
    def __init__(self, location: str = "./tests/data", filename: str = "system_card.yaml") -> None:
        self.location = location
        if not filename.endswith(".yaml"):
            raise ValueError(f"Filename {filename} must end with .yaml instead of .{filename.split('.')[-1]}")
        self.filename = filename

    def write(self, data: dict):
        if not Path(self.location).exists():
            Path(self.location).mkdir()
        with open(Path(self.location) / self.filename, "w") as f:
            dump(data, f, default_flow_style=False, sort_keys=False)

    def close(self):
        """
        This method is empty because with the `with` statement in the writer, Python will already close the writer
        after usage.
        """


class GitWriteService(WriterFactory):
    def __init__(self, kwargs):
        raise NotImplementedError

    def write(self, data):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError


class S3WriteService(WriterFactory):
    def __init__(self, kwargs):
        raise NotImplementedError

    def write(self, data):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
