from fastapi.testclient import TestClient


def test_get_root(client: TestClient) -> None:
    response = client.get(
        "/",
    )
    # todo (robbert) this is a quick test to see if we (most likely) get the expected page
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"<title>This is the page title</title>" in response.content


def test_get_favicon(client: TestClient) -> None:
    response = client.get(
        "/favicon.ico",
    )
    assert response.status_code == 200
