from fastapi.testclient import TestClient
from tad.schema.task import MovedTask

from tests.constants import all_statusses, default_task
from tests.database_test_utils import DatabaseTestUtils


def test_post_move_task(client: TestClient, db: DatabaseTestUtils) -> None:
    db.given([*all_statusses()])
    db.given([default_task(), default_task(), default_task()])

    move_task: MovedTask = MovedTask(taskId=2, statusId=2, previousSiblingId=1, nextSiblingId=3)

    response = client.patch("/tasks/", json=move_task.model_dump(by_alias=True))
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b'class="progress_card_container"' in response.content


def test_post_move_task_no_siblings(client: TestClient, db: DatabaseTestUtils) -> None:
    db.given([*all_statusses()])
    db.given([default_task(), default_task(), default_task()])

    move_task: MovedTask = MovedTask(taskId=2, statusId=1, previousSiblingId=-1, nextSiblingId=-1)
    response = client.patch("/tasks/", json=move_task.model_dump(by_alias=True))

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b'class="progress_card_container"' in response.content
