from fastapi.testclient import TestClient
from tad.models.task import MoveTask


def test_get_root(client: TestClient) -> None:
    move_task: MoveTask = MoveTask(taskId="2", statusId="2", previousSiblingId="1", nextSiblingId="3")
    print(move_task.model_dump_json(by_alias=True))
    response = client.post("/tasks/move", json=move_task.model_dump(by_alias=True))
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    # assert b"<h1>Welcome to the Home Page</h1>" in response.content
