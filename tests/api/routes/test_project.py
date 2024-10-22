from collections.abc import Generator
from typing import Any

import pytest
from amt.api.routes.project import set_path
from amt.models import Project
from fastapi.testclient import TestClient

from tests.constants import default_project, default_task
from tests.database_test_utils import DatabaseTestUtils
from fastapi_csrf_protect import CsrfProtect  # type: ignore # noqa


def test_get_unknown_project(client: TestClient) -> None:
    # when
    response = client.get("/algorithm-system/1")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


def test_get_project_tasks(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1"), default_task(project_id=1, status_id=1)])

    # when
    response = client.get("/algorithm-system/1/details/tasks")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Default Task" in response.content


# TODO: Test are now have hard coded URL paths because the system card
# is fixed for now. Tests need to be refactored and made proper once
# the actual stored system card in a project is being rendered.
def test_get_system_card(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1")])

    # when
    response = client.get("/algorithm-system/1/details/system_card")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"System card" in response.content


# TODO: Test are now have hard coded URL paths because the system card
# is fixed for now. Tests need to be refactored and made proper once
# the actual stored system card in a project is being rendered.
def test_get_system_card_unknown_project(client: TestClient) -> None:
    # when
    response = client.get("/algorithm-system/1/details/system_card")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


# TODO: Test are now have hard coded URL paths because the system card
# is fixed for now. Tests need to be refactored and made proper once
# the actual stored system card in a project is being rendered.
def test_get_assessment_card(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1")])

    # when
    response = client.get("/algorithm-system/1/details/system_card/assessments/iama")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Assessment card" in response.content


# TODO: Test are now have hard coded URL paths because the system card
# is fixed for now. Tests need to be refactored and made proper once
# the actual stored system card in a project is being rendered.
def test_get_assessment_card_unknown_project(client: TestClient) -> None:
    # when
    response = client.get("/algorithm-system/1/details/system_card/assessments/iama")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


# TODO: Test are now have hard coded URL paths because the system card
# is fixed for now. Tests need to be refactored and made proper once
# the actual stored system card in a project is being rendered.
def test_get_assessment_card_unknown_assessment(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1")])

    # when
    response = client.get("/algorithm-system/1/details/system_card/assessments/nonexistent")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


# TODO: Test are now have hard coded URL paths because the system card
# is fixed for now. Tests need to be refactored and made proper once
# the actual stored system card in a project is being rendered.
def test_get_model_card(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1")])

    # when
    response = client.get("/algorithm-system/1/details/system_card/models/logres_iris")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Model card" in response.content


# TODO: Test are now have hard coded URL paths because the system card
# is fixed for now. Tests need to be refactored and made proper once
# the actual stored system card in a project is being rendered.
def test_get_model_card_unknown_project(client: TestClient) -> None:
    # when
    response = client.get("/algorithm-system/1/details/system_card/models/logres_iris")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


# TODO: Test are now have hard coded URL paths because the system card
# is fixed for now. Tests need to be refactored and made proper once
# the actual stored system card in a project is being rendered.
def test_get_assessment_card_unknown_model_card(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1")])

    # when
    response = client.get("/algorithm-system/1/details/system_card/models/nonexistent")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


def test_get_project_details(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1"), default_task(project_id=1, status_id=1)])

    # when
    response = client.get("/algorithm-system/1/details")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Details" in response.content


def test_get_system_card_requirements(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1"), default_task(project_id=1, status_id=1)])

    # when
    response = client.get("/algorithm-system/1/details/system_card/requirements")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"0" in response.content


def test_get_system_card_data_page(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1"), default_task(project_id=1, status_id=1)])

    # when
    response = client.get("/algorithm-system/1/details/system_card/data")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"To be implemented" in response.content


def test_get_system_card_instruments(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1"), default_task(project_id=1, status_id=1)])

    # when
    response = client.get("/algorithm-system/1/details/system_card/instruments")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"To be implemented" in response.content


def test_get_project_edit(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1")])

    # when
    response = client.get("/algorithm-system/1/edit/system_card/lifecycle")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Save" in response.content
    assert b"lifecycle" in response.content


def test_get_project_cancel(client: TestClient, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1")])

    # when
    response = client.get("/algorithm-system/1/cancel/system_card/lifecycle")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Edit" in response.content
    assert b"lifecycle" in response.content


def test_get_project_update(client: TestClient, mocker, db: DatabaseTestUtils) -> None:
    # given
    db.given([default_project("testproject1")])
    client.cookies["fastapi-csrf-token"] = "1"
    CsrfProtect.validate_csrf = mocker.AsyncMock()

    # when
    response = client.put("/algorithm-system/1/update/name", json={"value": "Test Name"}, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"name" in response.content
    assert b"Test Name" in response.content

    # Verify that the project was updated in the database
    updated_projects = db.get(Project, "id", 1)
    assert len(updated_projects) == 1
    updated_project = updated_projects[0]
    assert updated_project.name == "Test Name"  # type: ignore


class DummyObject:
    pass


def test_set_path():  # type: ignore
    # Test with dictionary input
    project_dict: dict[str, Any] = {}
    set_path(project_dict, "/a/b/c", "value1")  # type: ignore
    assert project_dict == {"a": {"b": {"c": "value1"}}}

    # Test with nested dictionary input
    project_dict: dict[str, Any] = {"x": {"y": {}}}
    set_path(project_dict, "/x/y/z", "value2")
    assert project_dict == {"x": {"y": {"z": "value2"}}}

    # Test with object input
    project_obj: DummyObject = DummyObject()
    set_path(project_obj, "/a/b/c", "value3")
    assert hasattr(project_obj, "a")
    assert project_obj.a == {"b": {"c": "value3"}}  # type: ignore

    # Test with mixed object and dictionary input
    project_obj = DummyObject()
    project_obj.x = {}  # type: ignore
    set_path(project_obj, "/x/y/z", "value4")
    assert isinstance(project_obj.x, dict)  # type: ignore
    assert project_obj.x == {"y": {"z": "value4"}}  # type: ignore

    # Test with existing attributes
    project_obj: DummyObject = DummyObject()
    project_obj.a = DummyObject()  # type: ignore
    project_obj.a.b = "old_value"  # type: ignore
    set_path(project_obj, "/a/b", "new_value")
    assert project_obj.a.b == "new_value"  # type: ignore

    # Test with empty path
    project_dict: dict[str, Any] = {}
    with pytest.raises(ValueError):  # noqa: PT011
        set_path(project_dict, "", "value")

    # Test with root-level path
    project_dict: dict[str, Any] = {}
    set_path(project_dict, "/root", "value5")
    assert project_dict == {"root": "value5"}
