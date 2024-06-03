from fastapi.testclient import TestClient

from tests.database_test_utils import DatabaseTestUtils


def test_get_main_page(client: TestClient, db: DatabaseTestUtils) -> None:
    db.init(
        [
            {"table": "status", "id": 1},
            {"table": "task", "id": 1, "status_id": 1},
            {"table": "task", "id": 2, "status_id": 1},
        ]
    )
    response = client.get("/pages/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"<!DOCTYPE html>" in response.content
