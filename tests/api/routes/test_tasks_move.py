from fastapi.testclient import TestClient

from tests.constants import all_statusses, default_task
from tests.database_test_utils import DatabaseTestUtils


def test_post_task_move(client: TestClient, db: DatabaseTestUtils) -> None:
    db.given([*all_statusses()])
    db.given([default_task(), default_task(), default_task()])

    response = client.patch(
        "/tasks/", json={"taskId": "1", "statusId": "1", "previousSiblingId": "2", "nextSiblingId": "-1"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b'id="card-1"' in response.content


def test_task_move_error(client: TestClient) -> None:
    response = client.patch(
        "/tasks/", json={"taskId": "1", "statusId": "1", "previousSiblingId": "2", "nextSiblingId": "-1"}
    )
    assert response.status_code == 500
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"This is an error message" in response.content
