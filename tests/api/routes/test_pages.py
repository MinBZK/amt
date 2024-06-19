from fastapi.testclient import TestClient

from tests.constants import all_statusses, default_task
from tests.database_test_utils import DatabaseTestUtils


def test_get_main_page(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([*all_statusses(), default_task()])

    # when
    response = client.get("/pages/")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"<!DOCTYPE html>" in response.content
