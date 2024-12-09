from typing import Any

import pytest
import vcr  # type: ignore
from amt.api.routes.algorithm import (
    MeasureUpdate,
    find_measure_task,
    find_requirement_task,
    find_requirement_tasks_by_measure_urn,
    get_algorithm_context,
    get_algorithm_or_error,
    set_path,
)
from amt.core.exceptions import AMTNotFound, AMTRepositoryError
from amt.models import Algorithm
from amt.schema.task import MovedTask
from httpx import AsyncClient
from pytest_mock import MockFixture

from tests.api.routes.test_algorithms import MockRequest
from tests.constants import (
    default_algorithm,
    default_algorithm_with_system_card,
    default_task,
    default_user,
)
from tests.database_test_utils import DatabaseTestUtils


@pytest.mark.asyncio
async def test_get_unknown_algorithm(client: AsyncClient) -> None:
    # when
    response = await client.get("/algorithm/1/details")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
async def test_get_algorithm_tasks(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1"), default_task(algorithm_id=1, status_id=1)])

    # when
    response = await client.get("/algorithm/1/details/tasks")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Default Task" in response.content


@pytest.mark.asyncio
async def test_get_algorithm_inference(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1"), default_task(algorithm_id=1, status_id=1)])

    # when
    response = await client.get("/algorithm/1/details/model/inference")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b'<button id="runInference"' in response.content


@pytest.mark.asyncio
async def test_move_task(client: AsyncClient, db: DatabaseTestUtils, mocker: MockFixture) -> None:
    # given
    await db.given(
        [
            default_user(),
            default_algorithm("testalgorithm1"),
            default_task(algorithm_id=1, status_id=1),
            default_task(algorithm_id=1, status_id=1),
        ]
    )
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    client.cookies["fastapi-csrf-token"] = "1"

    # All -1 flow
    move_task_json = MovedTask(taskId=1, statusId=1, previousSiblingId=-1, nextSiblingId=-1).model_dump(by_alias=True)
    response = await client.patch("/algorithm/move_task", json=move_task_json, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Default Task" in response.content

    # All 1 flow
    move_task_json = MovedTask(taskId=1, statusId=1, previousSiblingId=1, nextSiblingId=1).model_dump(by_alias=True)
    response = await client.patch("/algorithm/move_task", json=move_task_json, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Default Task" in response.content


@pytest.mark.asyncio
async def test_get_algorithm_context(client: AsyncClient, db: DatabaseTestUtils, mocker: MockFixture) -> None:
    # given
    test_algorithm = default_algorithm_with_system_card("testalgorithm1")
    algorithm_service = mocker.AsyncMock()
    algorithm_service.get.return_value = test_algorithm

    algorithm, algorithm_context = await get_algorithm_context(
        algorithm_id=1, algorithms_service=algorithm_service, request=MockRequest("nl", url="/")
    )
    assert algorithm_context["last_edited"] is None
    assert algorithm == test_algorithm


@pytest.mark.asyncio
async def test_get_algorithm_non_existing_algorithm(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1"), default_task(algorithm_id=1, status_id=1)])

    # when
    response = await client.get("/algorithm/99/details/tasks")

    # then
    assert response.status_code == 404
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
async def test_get_algorithm_or_error(client: AsyncClient, db: DatabaseTestUtils, mocker: MockFixture) -> None:
    # given
    test_algorithm = default_algorithm("testalgorithm1")
    algorithm_service = mocker.AsyncMock()
    algorithm_service.get.return_value = test_algorithm

    # happy flow
    algorithm = await get_algorithm_or_error(
        algorithm_id=1, algorithms_service=algorithm_service, request=mocker.AsyncMock()
    )
    assert algorithm == test_algorithm

    # unhappy flow
    algorithm_service.get.side_effect = AMTRepositoryError
    with pytest.raises(AMTNotFound):
        _ = await get_algorithm_or_error(
            algorithm_id=99, algorithms_service=algorithm_service, request=mocker.AsyncMock()
        )


# TODO: Test are now have hard coded URL paths because the system card
# is fixed for now. Tests need to be refactored and made proper once
# the actual stored system card in a algorithm is being rendered.
@pytest.mark.asyncio
async def test_get_system_card(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/details/system_card")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"System card" in response.content


# TODO: Test are now have hard coded URL paths because the system card
# is fixed for now. Tests need to be refactored and made proper once
# the actual stored system card in a algorithm is being rendered.
@pytest.mark.asyncio
async def test_get_system_card_unknown_algorithm(client: AsyncClient) -> None:
    # when
    response = await client.get("/algorithm/1/details/system_card")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
@vcr.use_cassette("tests/fixtures/vcr_cassettes/test_get_assessment_card.yml")  # type: ignore
async def test_get_assessment_card(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm_with_system_card("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/details/system_card/assessments/iama")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Assessment card" in response.content


@pytest.mark.asyncio
async def test_get_assessment_card_unknown_algorithm(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/details/system_card/assessments/iama")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
async def test_get_assessment_card_unknown_assessment(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/details/system_card/assessments/nonexistent")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
@vcr.use_cassette("tests/fixtures/vcr_cassettes/test_get_model_card.yml")  # type: ignore
async def test_get_model_card(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm_with_system_card("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/details/system_card/models/logres_iris")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Model card" in response.content


async def test_get_model_card_unknown_algorithm(client: AsyncClient) -> None:
    # when
    response = await client.get("/algorithm/1/details/system_card/models/logres_iris")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
async def test_get_assessment_card_unknown_model_card(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/details/system_card/models/nonexistent")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The requested page or resource could not be found." in response.content


@pytest.mark.asyncio
async def test_get_algorithm_details(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1"), default_task(algorithm_id=1, status_id=1)])

    # when
    response = await client.get("/algorithm/1/details")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Details" in response.content


@pytest.mark.asyncio
@vcr.use_cassette("tests/fixtures/vcr_cassettes/test_get_system_card_requirements.yml")  # type: ignore
async def test_get_system_card_requirements(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given(
        [
            default_user(),
            default_algorithm_with_system_card("testalgorithm1"),
            default_task(algorithm_id=1, status_id=1),
        ]
    )

    # when
    response = await client.get("/algorithm/1/details/system_card/requirements")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"0" in response.content


@pytest.mark.asyncio
@vcr.use_cassette("tests/fixtures/vcr_cassettes/test_get_system_card_data_page.yml")  # type: ignore
async def test_get_system_card_data_page(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given(
        [
            default_user(),
            default_algorithm_with_system_card("testalgorithm1"),
            default_task(algorithm_id=1, status_id=1),
        ]
    )

    # when
    response = await client.get("/algorithm/1/details/system_card/data")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"To be implemented" in response.content


@pytest.mark.asyncio
@vcr.use_cassette("tests/fixtures/vcr_cassettes/test_get_system_card_instruments.yml")  # type: ignore
async def test_get_system_card_instruments(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given(
        [
            default_user(),
            default_algorithm_with_system_card("testalgorithm1"),
            default_task(algorithm_id=1, status_id=1),
        ]
    )

    # when
    response = await client.get("/algorithm/1/details/system_card/instruments")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"To be implemented" in response.content


@pytest.mark.asyncio
async def test_get_algorithm_edit(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/edit/system_card/lifecycle")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Save" in response.content
    assert b"lifecycle" in response.content


@pytest.mark.asyncio
async def test_delete_algorithm(client: AsyncClient, db: DatabaseTestUtils, mocker: MockFixture) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1")])
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    client.cookies["fastapi-csrf-token"] = "1"

    # when
    response = await client.delete("/algorithm/1", headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "hx-redirect" in response.headers
    assert response.headers["hx-redirect"] == "/algorithms/"


@pytest.mark.asyncio
async def test_delete_algorithm_and_check_list(client: AsyncClient, db: DatabaseTestUtils, mocker: MockFixture) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1"), default_algorithm("testalgorithm2")])
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    client.cookies["fastapi-csrf-token"] = "1"

    # when
    response = await client.delete("/algorithm/1", headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "hx-redirect" in response.headers

    response2 = await client.get("/algorithms/")
    assert response2.status_code == 200
    assert response2.headers["content-type"] == "text/html; charset=utf-8"
    assert b"testalgorithm2" in response2.content
    assert b"testalgorithm1" not in response2.content


@pytest.mark.asyncio
async def test_delete_algorithm_and_check_algorithm(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockFixture
) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1"), default_algorithm("testalgorithm2")])
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    client.cookies["fastapi-csrf-token"] = "1"

    # when
    response = await client.delete("/algorithm/1", headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "hx-redirect" in response.headers

    response2 = await client.get("/algorithm/1/details")
    assert response2.status_code == 404


@pytest.mark.asyncio
async def test_get_algorithm_cancel(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/cancel/system_card/lifecycle")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_get_algorithm_update(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1")])
    client.cookies["fastapi-csrf-token"] = "1"
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    # when
    response = await client.put("/algorithm/1/update/name", json={"value": "Test Name"}, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"name" in response.content
    assert b"Test Name" in response.content

    # Verify that the algorithm was updated in the database
    updated_algorithms = await db.get(Algorithm, "id", 1)
    assert len(updated_algorithms) == 1
    updated_algorithm = updated_algorithms[0]
    assert updated_algorithm.name == "Test Name"  # type: ignore


class DummyObject:
    pass


def test_set_path():  # type: ignore
    # Test with dictionary input
    algorithm_dict: dict[str, Any] = {}
    set_path(algorithm_dict, "/a/b/c", "value1")  # type: ignore
    assert algorithm_dict == {"a": {"b": {"c": "value1"}}}

    # Test with nested dictionary input
    algorithm_dict: dict[str, Any] = {"x": {"y": {}}}
    set_path(algorithm_dict, "/x/y/z", "value2")
    assert algorithm_dict == {"x": {"y": {"z": "value2"}}}

    # Test with object input
    algorithm_obj: DummyObject = DummyObject()
    set_path(algorithm_obj, "/a/b/c", "value3")
    assert hasattr(algorithm_obj, "a")
    assert algorithm_obj.a == {"b": {"c": "value3"}}  # type: ignore

    # Test with mixed object and dictionary input
    algorithm_obj = DummyObject()
    algorithm_obj.x = {}  # type: ignore
    set_path(algorithm_obj, "/x/y/z", "value4")
    assert isinstance(algorithm_obj.x, dict)  # type: ignore
    assert algorithm_obj.x == {"y": {"z": "value4"}}  # type: ignore

    # Test with existing attributes
    algorithm_obj: DummyObject = DummyObject()
    algorithm_obj.a = DummyObject()  # type: ignore
    algorithm_obj.a.b = "old_value"  # type: ignore
    set_path(algorithm_obj, "/a/b", "new_value")
    assert algorithm_obj.a.b == "new_value"  # type: ignore

    # Test with empty path
    algorithm_dict: dict[str, Any] = {}
    with pytest.raises(ValueError):  # noqa: PT011
        set_path(algorithm_dict, "", "value")

    # Test with root-level path
    algorithm_dict: dict[str, Any] = {}
    set_path(algorithm_dict, "/root", "value5")
    assert algorithm_dict == {"root": "value5"}


@pytest.mark.asyncio
async def test_find_measure_task() -> None:
    test_algorithm = default_algorithm_with_system_card("testalgorithm1")

    # no matched measure
    measure = find_measure_task(test_algorithm.system_card, "")
    assert measure is None

    # matches measure
    measure = find_measure_task(test_algorithm.system_card, "urn:nl:ak:mtr:dat-01")
    assert measure.urn == "urn:nl:ak:mtr:dat-01"  # pyright: ignore [reportOptionalMemberAccess]
    assert measure.value is not None  # pyright: ignore [reportOptionalMemberAccess]

    # no measures in system_card
    test_algorithm.system_card.measures = []
    measure = find_measure_task(test_algorithm.system_card, "")
    assert measure is None


@pytest.mark.asyncio
async def test_find_requirement_task() -> None:
    test_algorithm = default_algorithm_with_system_card("testalgorithm1")

    # no matched requirement
    requirement = find_requirement_task(test_algorithm.system_card, "")
    assert requirement is None

    # matches measure
    requirement = find_requirement_task(test_algorithm.system_card, "urn:nl:ak:ver:aia-05")
    assert requirement.urn == "urn:nl:ak:ver:aia-05"  # pyright: ignore [reportOptionalMemberAccess]
    assert requirement.state is not None  # pyright: ignore [reportOptionalMemberAccess]

    # no measures in system_card
    test_algorithm.system_card.requirements = []
    requirement = find_measure_task(test_algorithm.system_card, "")
    assert requirement is None


@pytest.mark.asyncio
async def test_find_requirement_tasks_by_measure_urn() -> None:
    test_algorithm = default_algorithm_with_system_card("testalgorithm1")

    # no matched requirement
    with pytest.raises(IndexError):
        # TODO: this is because it is not coded well change later
        requirement_tasks = await find_requirement_tasks_by_measure_urn(test_algorithm.system_card, "")

    # matches measure
    requirement_tasks = await find_requirement_tasks_by_measure_urn(test_algorithm.system_card, "urn:nl:ak:mtr:dat-01")
    assert len(requirement_tasks) == 2


@pytest.mark.asyncio
async def test_get_measure(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm_with_system_card("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/measure/urn:nl:ak:mtr:dat-01")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Controleer de datakwaliteit" in response.content


@pytest.mark.asyncio
async def test_update_measure_value(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm_with_system_card("testalgorithm1")])
    client.cookies["fastapi-csrf-token"] = "1"
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    # happy flow
    response = await client.post(
        "/algorithm/1/measure/urn:nl:ak:mtr:dat-01",
        json={"measure_update": MeasureUpdate(measure_state="done", measure_value="something").model_dump()},
        headers={"X-CSRF-Token": "1"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_download_algorithm_system_card_as_yaml(
    client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils
) -> None:
    # given
    await db.given([default_user(), default_algorithm_with_system_card("testalgorithm1")])
    client.cookies["fastapi-csrf-token"] = "1"
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    # happy flow
    response = await client.get("/algorithm/1/details/system_card/download")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert b"ai_act_profile:" in response.content
