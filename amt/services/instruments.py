import logging
from collections.abc import Sequence

from amt.clients.clients import TaskRegistryAPIClient
from amt.schema.instrument import Instrument

logger = logging.getLogger(__name__)


class InstrumentsService:
    def __init__(self) -> None:
        self.client = TaskRegistryAPIClient()

    def fetch_instruments(self, urns: str | Sequence[str] | None = None) -> list[Instrument]:
        """
        This functions returns instruments with given URN's. If urns contains an URN that is not a
        valid URN of an instrument it is simply ignored.

        @param: URN's of instruments to fetch. If empty, function returns all instruments.
        @return: List of instruments with given URN's in 'urns'.
        """

        if isinstance(urns, str):
            urns = [urns]

        all_valid_urns = self.fetch_urns()

        if urns is not None:
            return [self.client.get_instrument(urn) for urn in urns if urn in all_valid_urns]

        return [self.client.get_instrument(urn) for urn in all_valid_urns]

    def fetch_urns(self) -> list[str]:
        """
        Fetches all valid instrument URN's.
        """
        content_list = self.client.get_instrument_list()
        return [content.urn for content in content_list.root]
