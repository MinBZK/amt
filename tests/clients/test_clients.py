import pytest
from amt.clients.clients import get_client
from amt.schema.github import RepositoryContent
from httpx import HTTPStatusError
from pytest_httpx import HTTPXMock


def test_get_client_unknown_client():
    with pytest.raises(ValueError, match="unknown repository type: unknown_client"):
        get_client("unknown_client")


def test_get_content_github(httpx_mock: HTTPXMock):
    # given
    httpx_mock.add_response(
        url="https://api.github.com/stuff/123",
        content=b"somecontent",
        headers={"X-RateLimit-Remaining": "7", "X-RateLimit-Reset": "200000000"},
    )
    github_client = get_client("github")

    # when
    result = github_client.get_content("https://api.github.com/stuff/123")

    # then
    assert result == b"somecontent"


def test_list_content_github(httpx_mock: HTTPXMock):
    # given
    url = "https://api.github.com/repos/MinBZK/task-registry/contents/?ref=main"
    github_client = get_client("github")
    repository_content = RepositoryContent(root=[])

    httpx_mock.add_response(
        url=url,
        json=repository_content.model_dump(),
    )

    # when
    result = github_client.list_content(url)

    # then
    assert result == repository_content


def test_github_ratelimit_exceeded(httpx_mock: HTTPXMock):
    # given
    httpx_mock.add_response(
        url="https://api.github.com/stuff/123",
        status_code=403,
        headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "200000000"},
    )
    github_client = get_client("github")

    # when
    with pytest.raises(HTTPStatusError) as exc_info:
        github_client.get_content("https://api.github.com/stuff/123")

    # then
    assert "Client error '403 Forbidden'" in str(exc_info.value)


def test_get_content_github_pages(httpx_mock: HTTPXMock):
    # given
    httpx_mock.add_response(
        url="https://minbzk.github.io/stuff/123",
        content=b"somecontent",
    )
    github_client = get_client("github_pages")

    # when
    result = github_client.get_content("https://minbzk.github.io/stuff/123")

    # then
    assert result == b"somecontent"


def test_list_content_github_pages(httpx_mock: HTTPXMock):
    # given
    url = "https://minbzk.github.io/task-registry/index.json"
    github_client = get_client("github_pages")
    repository_content = RepositoryContent(root=[])
    input = {"entries": repository_content.model_dump()}

    httpx_mock.add_response(
        url=url,
        json=input,
    )

    # when
    result = github_client.list_content(url)

    # then
    assert result == repository_content
