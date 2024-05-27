from abc import ABC, abstractmethod
from typing import Dict

from yaml import dump


class Writer(ABC):
    def __init__(self, data: Dict, location: str):
        self.data = data
        self.location = location

    @abstractmethod
    def write(self) -> None:
        pass


class FileSystemWriter(Writer):
    def write(self):
        with open(self.location, "w") as f:
            dump(self.data, f, default_flow_style=False, sort_keys=False)


class GitWriter(Writer):
    def write(self):
        raise NotImplementedError


class S3Writer(Writer):
    def write(self):
        raise NotImplementedError


# system_card = SystemCard(name="iets")
# writer = FileSystemWriter(system_card.to_dict(), path)
# write.write()

# writer = FileSystemWriter(updated_system_card.to_dict(), path)
# writer.writer()

# Assume that to written system cards are the single source of truth.
# The logic for checking if writing to an existing system card is valid, should
# not be implemented in the writer?
