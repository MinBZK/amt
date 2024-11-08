from typing import Any

import pytest
from amt.api.routes.project import (
    MeasureUpdate,
    find_measure_task,
    find_requirement_task,
    find_requirement_tasks_by_measure_urn,
    get_project_context,
    get_project_or_error,
    set_path,
)
from amt.core.exceptions import AMTNotFound, AMTRepositoryError
from amt.models import Project
from amt.schema.task import MovedTask
from httpx import AsyncClient
from pytest_httpx import HTTPXMock
from pytest_mock import MockFixture

from tests.api.routes.test_projects import MockRequest
from tests.constants import (
    TASK_REGISTRY_AIIA_CONTENT_PAYLOAD,
    TASK_REGISTRY_CONTENT_PAYLOAD,
    TASK_REGISTRY_LIST_PAYLOAD,
    default_project,
    default_project_with_system_card,
    default_task,
)
from tests.database_test_utils import DatabaseTestUtils


@pytest.mark.asyncio
async def test_get_unknown_project(client: AsyncClient) -> None:
    # when
    response = await client.get("/algorithm-system/1")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
async def test_get_project_tasks(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_project("testproject1"), default_task(project_id=1, status_id=1)])

    # when
    response = await client.get("/algorithm-system/1/details/tasks")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Default Task" in response.content


@pytest.mark.asyncio
async def test_get_project_inference(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_project("testproject1"), default_task(project_id=1, status_id=1)])

    # when
    response = await client.get("/algorithm-system/1/details/model/inference")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b'<button id="runInference"' in response.content


@pytest.mark.asyncio
async def test_move_task(client: AsyncClient, db: DatabaseTestUtils, mocker: MockFixture) -> None:
    # given
    await db.given(
        [
            default_project("testproject1"),
            default_task(project_id=1, status_id=1),
            default_task(project_id=1, status_id=1),
        ]
    )
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    client.cookies["fastapi-csrf-token"] = "1"

    # All -1 flow
    move_task_json = MovedTask(taskId=1, statusId=1, previousSiblingId=-1, nextSiblingId=-1).model_dump(by_alias=True)
    response = await client.patch("/algorithm-system/move_task", json=move_task_json, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Default Task" in response.content

    # All 1 flow
    move_task_json = MovedTask(taskId=1, statusId=1, previousSiblingId=1, nextSiblingId=1).model_dump(by_alias=True)
    response = await client.patch("/algorithm-system/move_task", json=move_task_json, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Default Task" in response.content


@pytest.mark.asyncio
async def test_get_project_context(client: AsyncClient, db: DatabaseTestUtils, mocker: MockFixture) -> None:
    # given
    test_project = default_project_with_system_card("testproject1")
    project_service = mocker.AsyncMock()
    project_service.get.return_value = test_project

    project, project_context = await get_project_context(
        project_id=1, projects_service=project_service, request=MockRequest("nl", url="/")
    )
    assert project_context["last_edited"] is None
    assert project == test_project


@pytest.mark.asyncio
async def test_get_project_non_existing_project(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_project("testproject1"), default_task(project_id=1, status_id=1)])

    # when
    response = await client.get("/algorithm-system/99/details/tasks")

    # then
    assert response.status_code == 404
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
async def test_get_project_or_error(client: AsyncClient, db: DatabaseTestUtils, mocker: MockFixture) -> None:
    # given
    test_project = default_project("testproject1")
    project_service = mocker.AsyncMock()
    project_service.get.return_value = test_project

    # happy flow
    project = await get_project_or_error(project_id=1, projects_service=project_service, request=mocker.AsyncMock())
    assert project == test_project

    # unhappy flow
    project_service.get.side_effect = AMTRepositoryError
    with pytest.raises(AMTNotFound):
        _ = await get_project_or_error(project_id=99, projects_service=project_service, request=mocker.AsyncMock())


# TODO: Test are now have hard coded URL paths because the system card
# is fixed for now. Tests need to be refactored and made proper once
# the actual stored system card in a project is being rendered.
@pytest.mark.asyncio
async def test_get_system_card(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_project("testproject1")])

    # when
    response = await client.get("/algorithm-system/1/details/system_card")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"System card" in response.content


# TODO: Test are now have hard coded URL paths because the system card
# is fixed for now. Tests need to be refactored and made proper once
# the actual stored system card in a project is being rendered.
@pytest.mark.asyncio
async def test_get_system_card_unknown_project(client: AsyncClient) -> None:
    # when
    response = await client.get("/algorithm-system/1/details/system_card")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
async def test_get_assessment_card(client: AsyncClient, httpx_mock: HTTPXMock, db: DatabaseTestUtils) -> None:
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/", content=TASK_REGISTRY_LIST_PAYLOAD.encode()
    )
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/urn/urn:nl:aivt:tr:iama:1.0?version=latest",
        content=TASK_REGISTRY_CONTENT_PAYLOAD.encode(),
    )
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/urn/urn:nl:aivt:tr:aiia:1.0?version=latest",
        content=TASK_REGISTRY_AIIA_CONTENT_PAYLOAD.encode(),
    )
    # given
    await db.given([default_project_with_system_card("testproject1")])

    # when
    response = await client.get("/algorithm-system/1/details/system_card/assessments/iama")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Assessment card" in response.content


@pytest.mark.asyncio
async def test_get_assessment_card_unknown_project(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_project("testproject1")])

    # when
    response = await client.get("/algorithm-system/1/details/system_card/assessments/iama")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
async def test_get_assessment_card_unknown_assessment(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_project("testproject1")])

    # when
    response = await client.get("/algorithm-system/1/details/system_card/assessments/nonexistent")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
async def test_get_model_card(client: AsyncClient, httpx_mock: HTTPXMock, db: DatabaseTestUtils) -> None:
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/", content=TASK_REGISTRY_LIST_PAYLOAD.encode()
    )
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/urn/urn:nl:aivt:tr:iama:1.0?version=latest",
        content=TASK_REGISTRY_CONTENT_PAYLOAD.encode(),
    )
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/urn/urn:nl:aivt:tr:aiia:1.0?version=latest",
        content=TASK_REGISTRY_AIIA_CONTENT_PAYLOAD.encode(),
    )
    # given
    await db.given([default_project_with_system_card("testproject1")])

    # when
    response = await client.get("/algorithm-system/1/details/system_card/models/logres_iris")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Model card" in response.content


async def test_get_model_card_unknown_project(client: AsyncClient) -> None:
    # when
    response = await client.get("/algorithm-system/1/details/system_card/models/logres_iris")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
async def test_get_assessment_card_unknown_model_card(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_project("testproject1")])

    # when
    response = await client.get("/algorithm-system/1/details/system_card/models/nonexistent")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
async def test_get_project_details(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_project("testproject1"), default_task(project_id=1, status_id=1)])

    # when
    response = await client.get("/algorithm-system/1/details")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Details" in response.content


@pytest.mark.asyncio
async def test_get_system_card_requirements(client: AsyncClient, httpx_mock: HTTPXMock, db: DatabaseTestUtils) -> None:
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/", content=TASK_REGISTRY_LIST_PAYLOAD.encode()
    )
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/urn/urn:nl:aivt:tr:iama:1.0?version=latest",
        content=TASK_REGISTRY_CONTENT_PAYLOAD.encode(),
    )
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/urn/urn:nl:aivt:tr:aiia:1.0?version=latest",
        content=TASK_REGISTRY_AIIA_CONTENT_PAYLOAD.encode(),
    )
    # given
    await db.given([default_project_with_system_card("testproject1"), default_task(project_id=1, status_id=1)])

    # when
    response = await client.get("/algorithm-system/1/details/system_card/requirements")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"0" in response.content


@pytest.mark.asyncio
async def test_get_system_card_data_page(client: AsyncClient, httpx_mock: HTTPXMock, db: DatabaseTestUtils) -> None:
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/", content=TASK_REGISTRY_LIST_PAYLOAD.encode()
    )
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/urn/urn:nl:aivt:tr:iama:1.0?version=latest",
        content=TASK_REGISTRY_CONTENT_PAYLOAD.encode(),
    )
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/urn/urn:nl:aivt:tr:aiia:1.0?version=latest",
        content=TASK_REGISTRY_AIIA_CONTENT_PAYLOAD.encode(),
    )
    # given
    await db.given([default_project_with_system_card("testproject1"), default_task(project_id=1, status_id=1)])

    # when
    response = await client.get("/algorithm-system/1/details/system_card/data")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"To be implemented" in response.content


@pytest.mark.asyncio
async def test_get_system_card_instruments(client: AsyncClient, httpx_mock: HTTPXMock, db: DatabaseTestUtils) -> None:
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/", content=TASK_REGISTRY_LIST_PAYLOAD.encode()
    )
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/urn/urn:nl:aivt:tr:iama:1.0?version=latest",
        content=TASK_REGISTRY_CONTENT_PAYLOAD.encode(),
    )
    httpx_mock.add_response(
        url="https://task-registry.apps.digilab.network/instruments/urn/urn:nl:aivt:tr:aiia:1.0?version=latest",
        content=TASK_REGISTRY_AIIA_CONTENT_PAYLOAD.encode(),
    )
    # given
    await db.given([default_project_with_system_card("testproject1"), default_task(project_id=1, status_id=1)])

    # when
    response = await client.get("/algorithm-system/1/details/system_card/instruments")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"To be implemented" in response.content


@pytest.mark.asyncio
async def test_get_project_edit(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_project("testproject1")])

    # when
    response = await client.get("/algorithm-system/1/edit/system_card/lifecycle")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Save" in response.content
    assert b"lifecycle" in response.content


@pytest.mark.asyncio
async def test_get_project_cancel(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_project("testproject1")])

    # when
    response = await client.get("/algorithm-system/1/cancel/system_card/lifecycle")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Edit" in response.content
    assert b"lifecycle" in response.content


@pytest.mark.asyncio
async def test_get_project_update(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_project("testproject1")])
    client.cookies["fastapi-csrf-token"] = "1"
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    # when
    response = await client.put(
        "/algorithm-system/1/update/name", json={"value": "Test Name"}, headers={"X-CSRF-Token": "1"}
    )

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"name" in response.content
    assert b"Test Name" in response.content

    # Verify that the project was updated in the database
    updated_projects = await db.get(Project, "id", 1)
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


@pytest.mark.asyncio
async def test_find_measure_task() -> None:
    test_project = default_project_with_system_card("testproject1")

    # no matched measure
    measure = find_measure_task(test_project.system_card, "")
    assert measure is None

    # matches measure
    measure = find_measure_task(test_project.system_card, "urn:nl:ak:mtr:bnd-01")
    assert measure.urn == "urn:nl:ak:mtr:bnd-01"  # pyright: ignore [reportOptionalMemberAccess]
    assert measure.value is not None  # pyright: ignore [reportOptionalMemberAccess]

    # no measures in system_card
    test_project.system_card.measures = []
    measure = find_measure_task(test_project.system_card, "")
    assert measure is None


@pytest.mark.asyncio
async def test_find_requirement_task() -> None:
    test_project = default_project_with_system_card("testproject1")

    # no matched requirement
    requirement = find_requirement_task(test_project.system_card, "")
    assert requirement is None

    # matches measure
    requirement = find_requirement_task(test_project.system_card, "urn:nl:ak:ver:aia-05")
    assert requirement.urn == "urn:nl:ak:ver:aia-05"  # pyright: ignore [reportOptionalMemberAccess]
    assert requirement.state is not None  # pyright: ignore [reportOptionalMemberAccess]

    # no measures in system_card
    test_project.system_card.requirements = []
    requirement = find_measure_task(test_project.system_card, "")
    assert requirement is None


@pytest.mark.asyncio
async def test_find_requirement_tasks_by_measure_urn() -> None:
    test_project = default_project_with_system_card("testproject1")

    # no matched requirement
    with pytest.raises(IndexError):
        # TODO: this is because it is not coded well change later
        requirement_tasks = find_requirement_tasks_by_measure_urn(test_project.system_card, "")

    # matches measure
    requirement_tasks = find_requirement_tasks_by_measure_urn(test_project.system_card, "urn:nl:ak:mtr:bnd-01")
    assert len(requirement_tasks) == 3

    # empty requirements
    test_project.system_card.requirements = []
    with pytest.raises(KeyError):
        # TODO: this is because it is not coded well change later
        requirement_tasks = find_requirement_tasks_by_measure_urn(test_project.system_card, "urn:nl:ak:mtr:bnd-01")


@pytest.mark.asyncio
async def test_get_measure(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_project_with_system_card("testproject1")])

    # when
    response = await client.get("/algorithm-system/1/measure/urn:nl:ak:mtr:bnd-01")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Gebruik aselecte steekproeven" in response.content


@pytest.mark.asyncio
async def test_update_measure_value(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_project_with_system_card("testproject1")])
    client.cookies["fastapi-csrf-token"] = "1"
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    # happy flow
    response = await client.post(
        "/algorithm-system/1/measure/urn:nl:ak:mtr:bnd-01",
        json={"measure_update": MeasureUpdate(measure_state="done", measure_value="something").model_dump()},
        headers={"X-CSRF-Token": "1"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
