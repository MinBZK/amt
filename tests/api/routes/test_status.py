from collections.abc import Generator

from amt.schema.task import MovedTask
from fastapi.testclient import TestClient

from tests.constants import default_task, default_user
from tests.database_test_utils import DatabaseTestUtils


def test_post_move_task(client: TestClient, db: DatabaseTestUtils, mock_csrf: Generator[None, None, None]) -> None:
    db.given([default_task(), default_task(), default_task()])
    db.given([default_user()])
    client.cookies["fastapi-csrf-token"] = "1"

    move_task: MovedTask = MovedTask(taskId=2, statusId=2, previousSiblingId=1, nextSiblingId=3)

    response = client.patch("/tasks/", json=move_task.model_dump(by_alias=True), headers={"X-CSRF-Token": "1"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b'id="card-content-' in response.content


def test_post_move_task_no_siblings(
    client: TestClient,
    db: DatabaseTestUtils,
    mock_csrf: Generator[None, None, None],
) -> None:
    db.given([default_task(), default_task(), default_task()])
    client.cookies["fastapi-csrf-token"] = "1"

    move_task: MovedTask = MovedTask(taskId=2, statusId=1, previousSiblingId=-1, nextSiblingId=-1)
    response = client.patch("/tasks/", json=move_task.model_dump(by_alias=True), headers={"X-CSRF-Token": "1"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b'id="card-content-' in response.content
