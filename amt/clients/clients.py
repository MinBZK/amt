import logging

import httpx
from amt.core.exceptions import AMTInstrumentError, AMTNotFound
from amt.schema.github import RepositoryContent
from amt.schema.instrument import Instrument

logger = logging.getLogger(__name__)


class TaskRegistryAPIClient:
    """
    This class interacts with the Task Registry API.

    Currently it supports:
        - Retrieving the list of instruments.
        - Getting an instrument by URN.
    """

    base_url = "https://task-registry.apps.digilab.network"

    def __init__(self, max_retries: int = 3, timeout: int = 5) -> None:
        transport = httpx.HTTPTransport(retries=max_retries)
        self.client = httpx.Client(timeout=timeout, transport=transport)

    def get_instrument_list(self) -> RepositoryContent:
        response = self.client.get(f"{TaskRegistryAPIClient.base_url}/instruments/")
        if response.status_code != 200:
            raise AMTNotFound()
        return RepositoryContent.model_validate(response.json()["entries"])

    def get_instrument(self, urn: str, version: str = "latest") -> Instrument:
        response = self.client.get(
            f"{TaskRegistryAPIClient.base_url}/instruments/urn/{urn}", params={"version": version}
        )

        if response.status_code != 200:
            raise AMTNotFound()

        data = response.json()
        if "urn" not in data:
            logger.exception("Invalid instrument fetched: key 'urn' must occur in instrument.")
            raise AMTInstrumentError()

        return Instrument(**data)
