from fastapi.testclient import TestClient


def test_sts_header(client: TestClient) -> None:
    response = client.get(
        "/",
    )
    assert response.status_code == 200
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
