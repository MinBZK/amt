from fastapi.testclient import TestClient
from tad.models.task import MoveTask


def test_get_root(client: TestClient) -> None:
    move_task: MoveTask = MoveTask(taskId="1", statusId="2", previousSiblingId="3", nextSiblingId="4")
    print(move_task.model_dump())
    response = client.post("/tasks/move", data=move_task.model_dump())
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"

    assert b"<h1>Welcome to the Home Page</h1>" in response.content
