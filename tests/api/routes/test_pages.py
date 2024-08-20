from fastapi.testclient import TestClient

from tests.database_test_utils import DatabaseTestUtils


def test_get_main_page(client: TestClient, db: DatabaseTestUtils) -> None:
    # when
    response = client.get("/pages/")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"<!doctype html>" in response.content.lower()
