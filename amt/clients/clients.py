import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import httpx
from amt.schema.github import RepositoryContent

logger = logging.getLogger(__name__)


class Client(ABC):
    """
    Abstract class which is used to set up HTTP clients that retrieve instruments from the
    task registry.
    """

    @abstractmethod
    def __init__(self, max_retries: int = 3, timeout: int = 5) -> None:
        transport = httpx.HTTPTransport(retries=max_retries)
        self.client = httpx.Client(timeout=timeout, transport=transport)

    @abstractmethod
    def get_content(self, url: str) -> bytes:
        """
        This method should implement getting the content of an instrument from given URL.
        """

    @abstractmethod
    def list_content(self, url: str = "") -> RepositoryContent:
        """
        This method should implement getting list of instruments from given URL.
        """

    def _get(self, url: str) -> httpx.Response:
        """
        Private function that performs a GET request to given URL.
        """
        response = self.client.get(url)
        response.raise_for_status()
        return response


def get_client(repo_type: str) -> Client:
    match repo_type:
        case "github_pages":
            return GitHubPagesClient()
        case "github":
            return GitHubClient()
        case _:
            raise ValueError(f"unknown repository type: {repo_type}")


class GitHubPagesClient(Client):
    def __init__(self) -> None:
        super().__init__()

    def get_content(self, url: str) -> bytes:
        return super()._get(url).content

    def list_content(self, url: str = "https://minbzk.github.io/task-registry/index.json") -> RepositoryContent:
        response = super()._get(url)
        return RepositoryContent.model_validate(response.json()["entries"])


class GitHubClient(Client):
    def __init__(self) -> None:
        super().__init__()
        self.client.event_hooks["response"] = [self._check_rate_limit]
        # TODO(Berry): add authentication headers with event_hooks

    def get_content(self, url: str) -> bytes:
        return super()._get(url).content

    def list_content(
        self,
        url: str = "https://api.github.com/repos/MinBZK/task-registry/contents/instruments?ref=main",
    ) -> RepositoryContent:
        response = super()._get(url)
        return RepositoryContent.model_validate(response.json())

    def _check_rate_limit(self, response: httpx.Response) -> None:
        if "x-ratelimit-remaining" in response.headers:
            remaining = int(response.headers["X-RateLimit-Remaining"])
            if remaining == 0:
                reset_timestamp = int(response.headers["X-RateLimit-Reset"])
                reset_time = datetime.fromtimestamp(reset_timestamp, timezone.utc)  # noqa: UP017
                wait_seconds = (reset_time - datetime.now(timezone.utc)).total_seconds()  # noqa: UP017
                logger.warning(
                    f"Rate limit exceeded. We need to wait for {wait_seconds} seconds. (not implemented yet)"
                )
