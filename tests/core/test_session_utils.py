import pytest
from amt.core.session_utils import (
    PublishStep,
    clear_algoritmeregister_credentials,
    clear_publish_step,
    get_algoritmeregister_credentials,
    get_publish_step,
    set_publish_step,
    store_algoritmeregister_credentials,
)
from amt.schema.algoritmeregister import AlgoritmeregisterCredentials
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_store_and_get_algoritmeregister_credentials(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {}  # type: ignore
    mock_request.cookies = {}  # type: ignore
    credentials = AlgoritmeregisterCredentials(
        username="test_user",
        password="test_pass",  # noqa: S106
        organization_id="org123",
        token="test_token",  # noqa: S106
    )

    # when
    store_algoritmeregister_credentials(mock_request, credentials)
    result = get_algoritmeregister_credentials(mock_request)

    # then
    assert result == credentials
    assert mock_request.session["algoritmeregister_credentials"] == {  # type: ignore
        "username": "test_user",
        "password": "test_pass",
        "organization_id": "org123",
        "token": "test_token",
        "organisations": [],
    }


@pytest.mark.asyncio
async def test_get_algoritmeregister_credentials_returns_none_when_not_set(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {}  # type: ignore
    mock_request.cookies = {}  # type: ignore

    # when
    result = get_algoritmeregister_credentials(mock_request)

    # then
    assert result is None


@pytest.mark.asyncio
async def test_clear_algoritmeregister_credentials(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {}  # type: ignore
    mock_request.cookies = {}  # type: ignore
    credentials = AlgoritmeregisterCredentials(
        username="test_user",
        password="test_pass",  # noqa: S106
        organization_id="org123",
        token="test_token",  # noqa: S106
    )
    store_algoritmeregister_credentials(mock_request, credentials)

    # when
    clear_algoritmeregister_credentials(mock_request)
    result = get_algoritmeregister_credentials(mock_request)

    # then
    assert result is None
    assert "algoritmeregister_credentials" not in mock_request.session  # type: ignore


@pytest.mark.asyncio
async def test_clear_algoritmeregister_credentials_when_not_set(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {}  # type: ignore
    mock_request.cookies = {}  # type: ignore

    # when
    clear_algoritmeregister_credentials(mock_request)

    # then
    assert "algoritmeregister_credentials" not in mock_request.session  # type: ignore


@pytest.mark.asyncio
async def test_get_publish_step_returns_none_when_not_set(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {}  # type: ignore

    # when
    result = get_publish_step(mock_request, 1)

    # then
    assert result is None


@pytest.mark.asyncio
async def test_get_publish_step_returns_none_when_algorithm_not_in_steps(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {"publish_steps": {"2": "prepare"}}  # type: ignore

    # when
    result = get_publish_step(mock_request, 1)

    # then
    assert result is None


@pytest.mark.asyncio
async def test_set_and_get_publish_step(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {}  # type: ignore

    # when
    set_publish_step(mock_request, 1, PublishStep.PREPARE)
    result = get_publish_step(mock_request, 1)

    # then
    assert result == PublishStep.PREPARE
    assert mock_request.session["publish_steps"] == {"1": "prepare"}  # type: ignore


@pytest.mark.asyncio
async def test_set_publish_step_updates_existing(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {"publish_steps": {"1": "prepare"}}  # type: ignore

    # when
    set_publish_step(mock_request, 1, PublishStep.PREVIEW)
    result = get_publish_step(mock_request, 1)

    # then
    assert result == PublishStep.PREVIEW


@pytest.mark.asyncio
async def test_clear_publish_step(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {}  # type: ignore
    set_publish_step(mock_request, 1, PublishStep.PREPARE)

    # when
    clear_publish_step(mock_request, 1)
    result = get_publish_step(mock_request, 1)

    # then
    assert result is None


@pytest.mark.asyncio
async def test_clear_publish_step_when_not_set(mocker: MockerFixture) -> None:
    # given
    mock_request = mocker.Mock()
    mock_request.session = {}  # type: ignore

    # when
    clear_publish_step(mock_request, 1)

    # then
    assert mock_request.session == {}  # type: ignore
