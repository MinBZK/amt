import pytest
from amt.core.exceptions import AMTInstrumentError
from amt.services.instruments import InstrumentsService
from pytest_httpx import HTTPXMock
from tests.constants import (
    TASK_REGISTRY_CONTENT_PAYLOAD,
    TASK_REGISTRY_LIST_PAYLOAD,
)

# TODO(berry): made payloads to a better location


def test_fetch_urns(httpx_mock: HTTPXMock):
    # given
    instruments_service = InstrumentsService()
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/", content=TASK_REGISTRY_LIST_PAYLOAD.encode()
    )

    # when
    result = instruments_service.fetch_urns()

    # then
    assert len(result) == 1
    assert result[0] == "urn:nl:aivt:tr:iama:1.0"


def test_fetch_instruments(httpx_mock: HTTPXMock):
    # given
    instruments_service = InstrumentsService()
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/", content=TASK_REGISTRY_LIST_PAYLOAD.encode()
    )

    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/urns/?version=latest&urn=urn%3Anl%3Aaivt%3Atr%3Aiama%3A1.0",
        content=TASK_REGISTRY_CONTENT_PAYLOAD.encode(),
    )

    # when
    result = instruments_service.fetch_instruments()

    # then
    assert len(result) == 1


def test_fetch_instrument_with_urn(httpx_mock: HTTPXMock):
    # given
    instruments_service = InstrumentsService()
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/", content=TASK_REGISTRY_LIST_PAYLOAD.encode()
    )
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/urns/?version=latest&urn=urn%3Anl%3Aaivt%3Atr%3Aiama%3A1.0",
        content=TASK_REGISTRY_CONTENT_PAYLOAD.encode(),
    )

    # when
    urn = "urn:nl:aivt:tr:iama:1.0"
    result = instruments_service.fetch_instruments(urn)

    # then
    assert len(result) == 1


def test_fetch_instruments_with_urns(httpx_mock: HTTPXMock):
    # given
    instruments_service = InstrumentsService()
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/", content=TASK_REGISTRY_LIST_PAYLOAD.encode()
    )
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/urns/?version=latest&urn=urn%3Anl%3Aaivt%3Atr%3Aiama%3A1.0",
        content=TASK_REGISTRY_CONTENT_PAYLOAD.encode(),
    )

    # when
    urn = "urn:nl:aivt:tr:iama:1.0"
    result = instruments_service.fetch_instruments([urn])

    # then
    assert len(result) == 1


def test_fetch_instruments_with_invalid_urn(httpx_mock: HTTPXMock):
    # given
    instruments_service = InstrumentsService()
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/", content=TASK_REGISTRY_LIST_PAYLOAD.encode()
    )

    # when
    urn = "urn:nl:aivt:ir:iama:1.0"
    result = instruments_service.fetch_instruments([urn])

    # then
    assert len(result) == 0


def test_fetch_instruments_invalid(httpx_mock: HTTPXMock):
    # given
    instruments_service = InstrumentsService()
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/", content=TASK_REGISTRY_LIST_PAYLOAD.encode()
    )

    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/urns/?version=latest&urn=urn%3Anl%3Aaivt%3Atr%3Aiama%3A1.0",
        content=b'{"test": 1}',
    )

    # then
    pytest.raises(AMTInstrumentError, instruments_service.fetch_instruments)
