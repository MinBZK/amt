import pytest
from amt.clients.clients import TaskRegistryAPIClient, TaskType
from amt.core.exceptions import AMTInstrumentError
from amt.repositories.task_registry import TaskRegistryRepository
from pytest_httpx import HTTPXMock
from tests.conftest import amt_vcr


@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_fetch_tasks_all.yml")  # type: ignore
@pytest.mark.asyncio
async def test_fetch_tasks_all():
    # given
    client = TaskRegistryAPIClient()
    repository = TaskRegistryRepository(client)

    # when
    instrument_result = await repository.fetch_tasks(TaskType.INSTRUMENTS)
    requirement_result = await repository.fetch_tasks(TaskType.REQUIREMENTS)
    measure_result = await repository.fetch_tasks(TaskType.MEASURES)

    # then
    assert len(instrument_result) == 4
    assert len(requirement_result) == 63
    assert len(measure_result) == 105


@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_fetch_task_with_urn.yml")  # type: ignore
@pytest.mark.asyncio
async def test_fetch_task_with_urn():
    # given
    client = TaskRegistryAPIClient()
    repository = TaskRegistryRepository(client)
    instrument_urn = "urn:nl:aivt:tr:iama:1.0"
    requirement_urn = "urn:nl:ak:ver:aia-08"
    measure_urn = "urn:nl:ak:mtr:dat-02"

    # when
    instrument_result = await repository.fetch_tasks(TaskType.INSTRUMENTS, urns=instrument_urn)
    requirement_result = await repository.fetch_tasks(TaskType.REQUIREMENTS, urns=requirement_urn)
    measure_result = await repository.fetch_tasks(TaskType.MEASURES, urns=measure_urn)

    # then
    assert len(instrument_result) == 1
    assert "urn" in instrument_result[0]
    assert instrument_result[0]["urn"] == instrument_urn

    assert len(requirement_result) == 1
    assert "urn" in requirement_result[0]
    assert requirement_result[0]["urn"] == requirement_urn

    assert len(measure_result) == 1
    assert "urn" in measure_result[0]
    assert measure_result[0]["urn"] == measure_urn


@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_fetch_task_with_urns.yml")  # type: ignore
@pytest.mark.asyncio
async def test_fetch_task_with_urns():
    # given
    client = TaskRegistryAPIClient()
    repository = TaskRegistryRepository(client)
    urns = ["urn:nl:aivt:tr:iama:1.0", "urn:nl:aivt:tr:aiia:1.0"]

    # when
    result = await repository.fetch_tasks(TaskType.INSTRUMENTS, urns=urns)

    # then
    assert len(result) == 2
    assert "urn" in result[0]
    assert result[0]["urn"] == urns[0]
    assert "urn" in result[1]
    assert result[1]["urn"] == urns[1]


@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_fetch_task_with_invalid_urn.yml")  # type: ignore
@pytest.mark.asyncio
async def test_fetch_task_with_invalid_urn():
    # given
    client = TaskRegistryAPIClient()
    repository = TaskRegistryRepository(client)
    urn = "invalid"

    # when
    result = await repository.fetch_tasks(TaskType.INSTRUMENTS, urns=urn)

    # then
    assert len(result) == 0


@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_fetch_task_with_valid_and_invalid_urn.yml")  # type: ignore
@pytest.mark.asyncio
async def test_fetch_task_with_valid_and_invalid_urn():
    # given
    client = TaskRegistryAPIClient()
    repository = TaskRegistryRepository(client)
    urns = ["urn:nl:aivt:tr:iama:1.0", "invalid"]

    # when
    result = await repository.fetch_tasks(TaskType.INSTRUMENTS, urns=urns)

    # then
    assert len(result) == 1
    assert "urn" in result[0]
    assert result[0]["urn"] == urns[0]


@pytest.mark.asyncio
async def test_fetch_tasks_invalid_response(httpx_mock: HTTPXMock):
    # given
    client = TaskRegistryAPIClient()
    repository = TaskRegistryRepository(client)
    urn = "urn:nl:aivt:tr:td:1.0"

    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/urn/urn:nl:aivt:tr:td:1.0?version=latest",
        content=b'{"test": 1}',
        is_optional=True,
    )

    # then
    with pytest.raises(AMTInstrumentError):
        await repository.fetch_tasks(TaskType.INSTRUMENTS, urn)
