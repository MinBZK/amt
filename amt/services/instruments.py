import logging
from collections.abc import Sequence

import yaml

from amt.clients.clients import get_client
from amt.core.exceptions import InstrumentError
from amt.schema.github import RepositoryContent
from amt.schema.instrument import Instrument

logger = logging.getLogger(__name__)


class InstrumentsService:
    def __init__(self, repo_type: str = "github_pages") -> None:
        self.client = get_client(repo_type)

    def fetch_github_content_list(self) -> RepositoryContent:
        response = self.client.list_content()
        return RepositoryContent.model_validate(response)

    def fetch_github_content(self, url: str) -> Instrument:
        bytes_data = self.client.get_content(url)

        # assume yaml
        data = yaml.safe_load(bytes_data)

        if "urn" not in data:
            # todo: this is now an HTTP error, while a service can also be used from another context
            logger.exception("Key 'urn' not found in instrument.")
            raise InstrumentError("Key 'urn' not found in instrument.")

        return Instrument(**data)

    def fetch_instruments(self, urns: Sequence[str] | None = None) -> list[Instrument]:
        content_list = self.fetch_github_content_list()

        instruments: list[Instrument] = []

        for content in content_list.root:  # TODO(Berry): fix root field
            instrument = self.fetch_github_content(str(content.download_url))
            if urns is None:
                instruments.append(instrument)
            else:
                if instrument.urn in set(urns):
                    instruments.append(instrument)
        return instruments
