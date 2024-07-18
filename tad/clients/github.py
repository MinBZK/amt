import logging
from datetime import datetime, timezone

import httpx
from tad.schema.github import RepositoryContent

logger = logging.getLogger(__name__)


class GitHubClient:
    def __init__(self, base_url: str = "https://api.github.com", max_retries: int = 3, timeout: int = 5) -> None:
        self.base_url = base_url
        transport = httpx.HTTPTransport(retries=max_retries)
        self.client = httpx.Client(
            timeout=timeout, transport=transport, event_hooks={"response": [self._check_rate_limit]}
        )
        # TODO(Berry): add authentication headers with event_hooks

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

    def get_content(self, url: str) -> bytes:
        response = self.client.get(url)
        response.raise_for_status()
        return response.content

    def list_content(
        self, folder: str = "", org: str = "MinBZK", repo: str = "instrument-registry", branch: str = "main"
    ) -> RepositoryContent:
        url = f"{self.base_url}/repos/{org}/{repo}/contents/{folder}?ref={branch}"
        response = self.client.get(url)
        response.raise_for_status()

        repository_content = RepositoryContent.model_validate(response.json())
        return repository_content
