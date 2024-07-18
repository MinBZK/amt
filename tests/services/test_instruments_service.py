import pytest
from pytest_httpx import HTTPXMock
from tad.core.exceptions import InstrumentError
from tad.services.instruments import InstrumentsService
from tests.constants import GITHUB_CONTENT_PAYLOAD, GITHUB_LIST_PAYLOAD

# TODO(berry): made payloads to a better location


def test_fetch_instruments(httpx_mock: HTTPXMock):
    # given
    instruments_service = InstrumentsService()
    httpx_mock.add_response(
        url="https://api.github.com/repos/MinBZK/instrument-registry/contents/instruments?ref=main",
        content=GITHUB_LIST_PAYLOAD.encode(),
        headers={"X-RateLimit-Remaining": "7", "X-RateLimit-Reset": "200000000", "Content-Type": "application/json"},
    )

    httpx_mock.add_response(
        url="https://raw.githubusercontent.com/MinBZK/instrument-registry/main/instruments/iama.yaml",
        content=GITHUB_CONTENT_PAYLOAD.encode(),
        headers={"X-RateLimit-Remaining": "7", "X-RateLimit-Reset": "200000000", "content-type": "text/plain"},
    )

    # when
    result = instruments_service.fetch_instruments()

    # then
    assert len(result) == 1


def test_fetch_instruments_invalid(httpx_mock: HTTPXMock):
    # given
    instruments_service = InstrumentsService()
    httpx_mock.add_response(
        url="https://api.github.com/repos/MinBZK/instrument-registry/contents/instruments?ref=main",
        content=GITHUB_LIST_PAYLOAD.encode(),
        headers={"X-RateLimit-Remaining": "7", "X-RateLimit-Reset": "200000000", "Content-Type": "application/json"},
    )

    # when
    httpx_mock.add_response(
        url="https://raw.githubusercontent.com/MinBZK/instrument-registry/main/instruments/iama.yaml",
        content=b"test: 1",
        headers={"X-RateLimit-Remaining": "7", "X-RateLimit-Reset": "200000000", "content-type": "text/plain"},
    )

    # then
    pytest.raises(InstrumentError, instruments_service.fetch_instruments)
