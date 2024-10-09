import pytest
from amt.core.exceptions import AMTAuthorizationError
from fastapi.testclient import TestClient


@pytest.mark.enable_auth
def test_auth_not_project(client: TestClient) -> None:
    with pytest.raises(AMTAuthorizationError, match="401: Failed to authorize, please login and try again."):
        client.get("/projects/")
