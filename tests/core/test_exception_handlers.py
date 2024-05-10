import pytest
from fastapi import status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.testclient import TestClient
from tad.main import app


@pytest.fixture()
def _mock_error_500():
    """Add route to raise ValueError"""

    @app.get("/raise-http-exception")
    async def raise_http_error():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    @app.get("/raise-request-validation-exception")
    async def raise_request_error():
        raise RequestValidationError(errors=None)


@pytest.mark.usefixtures("_mock_error_500")
def test_http_exception_handler(client: TestClient):
    response = client.get("/raise-http-exception")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.usefixtures("_mock_error_500")
def test_request_validation_exception_handler(client: TestClient):
    response = client.get("/raise-request-validation-exception")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.headers["content-type"] == "text/html; charset=utf-8"
