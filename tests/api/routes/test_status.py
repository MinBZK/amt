from fastapi.testclient import TestClient
from tad.models.task import MoveTask

from tests.database_test_utils import DatabaseTestUtils


def test_post_move_task(client: TestClient, db: DatabaseTestUtils) -> None:
    db.init(
        [
            {"table": "status", "id": 2},
            {"table": "task", "id": 1, "status_id": 2},
            {"table": "task", "id": 2, "status_id": 2},
            {"table": "task", "id": 3, "status_id": 2},
        ]
    )
    move_task: MoveTask = MoveTask(taskId="2", statusId="2", previousSiblingId="1", nextSiblingId="3")
    response = client.post("/tasks/move", json=move_task.model_dump(by_alias=True))
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b'class="progress_card_container"' in response.content
