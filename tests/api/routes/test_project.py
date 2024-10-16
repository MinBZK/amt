from fastapi.testclient import TestClient

from tests.constants import default_project, default_task
from tests.database_test_utils import DatabaseTestUtils


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
