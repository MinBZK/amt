import logging

import yaml

from tad.clients.github import GitHubClient
from tad.core.exceptions import InstrumentError
from tad.schema.github import RepositoryContent
from tad.schema.instrument import Instrument

logger = logging.getLogger(__name__)


class InstrumentsService:
    def __init__(self) -> None:
        self.client = GitHubClient()

    def fetch_github_content_list(self, folder: str = "instruments") -> RepositoryContent:
        response = self.client.list_content(folder=folder)
        return RepositoryContent.model_validate(response)

    def fetch_github_content(self, url: str) -> Instrument:
        bytes_data = self.client.get_content(url)

        # assume yaml
        data = yaml.safe_load(bytes_data)

        if "instrument" not in data:
            raise InstrumentError()

        return Instrument(**data["instrument"])

    def fetch_instruments(self) -> list[Instrument]:
        content_list = self.fetch_github_content_list()

        instruments: list[Instrument] = []

        for content in content_list.root:  # TODO(Berry): fix root field
            instrument = self.fetch_github_content(str(content.download_url))
            instruments.append(instrument)
        return instruments

    #
