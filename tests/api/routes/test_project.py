from fastapi.testclient import TestClient

from tests.constants import default_project
from tests.database_test_utils import DatabaseTestUtils


def test_get_default_project(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1")])

    # when
    response = client.get("/project/1")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"testproject1" in response.content


def test_get_unknown_project(client: TestClient, db: DatabaseTestUtils) -> None:
    # when
    response = client.get("/project/1")

    print(response.content)

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"<h2>Not found</h2>" in response.content
