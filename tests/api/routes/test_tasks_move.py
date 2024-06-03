from fastapi.testclient import TestClient

from tests.database_test_utils import DatabaseTestUtils


def test_post_task_move(client: TestClient, db: DatabaseTestUtils) -> None:
    db.init(
        [
            {"table": "status", "id": 1},
            {"table": "task", "id": 1, "status_id": 1},
            {"table": "task", "id": 2, "status_id": 1},
        ]
    )
    response = client.post(
        "/tasks/move", json={"taskId": "1", "statusId": "1", "previousSiblingId": "2", "nextSiblingId": ""}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b'id="card-1"' in response.content


def test_post_task_move_error(client: TestClient, db: DatabaseTestUtils) -> None:
    db.init()
    response = client.post(
        "/tasks/move", json={"taskId": "1", "statusId": "1", "previousSiblingId": "2", "nextSiblingId": ""}
    )
    assert response.status_code == 500
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"This is an error message" in response.content
