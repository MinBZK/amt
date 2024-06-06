from fastapi.testclient import TestClient


def test_get_root(client: TestClient) -> None:
    response = client.get(
        "/",
        follow_redirects=False,
    )
    # todo (robbert) this is a quick test to see if we (most likely) get the expected page
    assert response.status_code == 307
