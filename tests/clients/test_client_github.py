import pytest
from amt.clients.github import GitHubClient
from amt.schema.github import RepositoryContent
from httpx import HTTPStatusError
from pytest_httpx import HTTPXMock


def test_get_content(httpx_mock: HTTPXMock):
    # given
    httpx_mock.add_response(
        url="https://api.github.com/stuff/123",
        content=b"somecontent",
        headers={"X-RateLimit-Remaining": "7", "X-RateLimit-Reset": "200000000"},
    )
    github_client = GitHubClient()

    # when
    result = github_client.get_content("https://api.github.com/stuff/123")

    # then
    assert result == b"somecontent"


def test_list_content(httpx_mock: HTTPXMock):
    # given
    base_url = "https://api.github.com"
    folder = ""
    org = "MinBZK"
    repo = "instrument-registry"
    branch = "main"
    github_client = GitHubClient()
    repository_content = RepositoryContent(root=[])

    httpx_mock.add_response(
        url=f"{base_url}/repos/{org}/{repo}/contents/{folder}?ref={branch}", json=repository_content.model_dump()
    )

    # when
    result = github_client.list_content(folder, org, repo, branch)

    # then
    assert result == repository_content


def test_github_ratelimit_exceeded(httpx_mock: HTTPXMock):
    # given
    httpx_mock.add_response(
        url="https://api.github.com/stuff/123",
        status_code=403,
        headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "200000000"},
    )
    github_client = GitHubClient()

    # when
    with pytest.raises(HTTPStatusError) as exc_info:
        github_client.get_content("https://api.github.com/stuff/123")

    # then
    assert "Client error '403 Forbidden'" in str(exc_info.value)
