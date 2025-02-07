from io import BytesIO
from typing import Any

import pytest
from amt.api.editable import set_path
from amt.api.routes.algorithm import (
    find_measure_task,
    find_requirement_task,
    find_requirement_tasks_by_measure_urn,
    get_algorithm_context,
    get_algorithm_or_error,
    get_user_id_or_error,
    resolve_and_enrich_measures,
)
from amt.core.config import get_settings
from amt.core.exceptions import AMTError, AMTNotFound, AMTRepositoryError
from amt.enums.tasks import TaskType
from amt.models import Algorithm
from amt.repositories.users import UsersRepository
from amt.schema.measure import MeasureTask
from amt.schema.task import MovedTask
from amt.services.object_storage import create_object_storage_service
from amt.services.users import UsersService
from fastapi import UploadFile
from httpx import AsyncClient
from minio import Minio
from pytest_minio_mock.plugin import MockMinioClient  # pyright: ignore [reportMissingTypeStubs]
from pytest_mock import MockFixture

from tests.api.routes.test_algorithms import MockRequest
from tests.conftest import amt_vcr
from tests.constants import (
    default_algorithm,
    default_algorithm_with_system_card,
    default_not_found_no_permission_msg,
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
    assert default_not_found_no_permission_msg() in response.content


@pytest.mark.asyncio
async def test_get_algorithm_tasks(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1"), default_task(algorithm_id=1, status_id=1)])

    # when
    response = await client.get("/algorithm/1/tasks")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Default Task" in response.content


@pytest.mark.asyncio
async def test_move_task(client: AsyncClient, db: DatabaseTestUtils, mocker: MockFixture) -> None:
    # given
    await db.given(
        [
            default_user(),
            default_algorithm_with_system_card("testalgorithm1"),
            default_task(algorithm_id=1, status_id=1),
            default_task(algorithm_id=1, status_id=1),
            default_task(algorithm_id=1, status_id=1, type=TaskType.MEASURE, type_id="urn:nl:ak:mtr:dat-01"),
        ]
    )
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    client.cookies["fastapi-csrf-token"] = "1"

    # All -1 flow
    move_task_json = MovedTask(taskId=1, statusId=1, previousSiblingId=-1, nextSiblingId=-1).model_dump(by_alias=True)
    response = await client.patch("/algorithm/1/move_task", json=move_task_json, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Default Task" in response.content

    # All 1 flow
    move_task_json = MovedTask(taskId=1, statusId=1, previousSiblingId=1, nextSiblingId=1).model_dump(by_alias=True)
    response = await client.patch("/algorithm/1/move_task", json=move_task_json, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Default Task" in response.content

    # All 1 flow
    move_task_json = MovedTask(taskId=3, statusId=1, previousSiblingId=1, nextSiblingId=1).model_dump(by_alias=True)
    response = await client.patch("/algorithm/1/move_task", json=move_task_json, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Controleer de datakwaliteit" in response.content


@pytest.mark.asyncio
@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_get_algorithm_context.yml")  # type: ignore
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
    assert default_not_found_no_permission_msg() in response.content


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


@pytest.mark.asyncio
async def test_get_system_card(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/info")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Does the algorithm meet the requirements?" in response.content


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
    assert default_not_found_no_permission_msg() in response.content


@pytest.mark.asyncio
@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_get_assessment_card.yml")  # type: ignore
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
    assert default_not_found_no_permission_msg() in response.content


@pytest.mark.asyncio
async def test_get_assessment_card_unknown_assessment(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/details/system_card/assessments/nonexistent")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert default_not_found_no_permission_msg() in response.content


@pytest.mark.asyncio
@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_get_model_card.yml")  # type: ignore
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
    assert default_not_found_no_permission_msg() in response.content


@pytest.mark.asyncio
async def test_get_assessment_card_unknown_model_card(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/details/system_card/models/nonexistent")

    # then
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert default_not_found_no_permission_msg() in response.content


@pytest.mark.asyncio
async def test_get_algorithm_details(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1"), default_task(algorithm_id=1, status_id=1)])

    # when
    response = await client.get("/algorithm/1/details")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Last updated" in response.content


@pytest.mark.asyncio
@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_get_system_card_compliance.yml")  # type: ignore
async def test_get_system_card_compliance(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given(
        [
            default_user(),
            default_algorithm_with_system_card("testalgorithm1"),
            default_task(algorithm_id=1, status_id=1),
        ]
    )

    # when
    response = await client.get("/algorithm/1/compliance")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"0" in response.content


@pytest.mark.asyncio
@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_get_algorithm_members.yml")  # type: ignore
async def test_get_algorithm_members(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given(
        [
            default_user(),
            default_algorithm_with_system_card("testalgorithm1"),
            default_task(algorithm_id=1, status_id=1),
        ]
    )

    # when
    response = await client.get("/algorithm/1/members")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_get_algorithm_edit(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/edit?full_resource_path=algorithm/1/system_card/name")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Save" in response.content
    assert b"name" in response.content


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
    response = await client.get("/algorithm/1/cancel?full_resource_path=algorithm/1/system_card/name")

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
    response = await client.put(
        "/algorithm/1/update?full_resource_path=algorithm/1/system_card/name",
        json={"name": "Test Name"},
        headers={"X-CSRF-Token": "1"},
    )

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
@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_find_requirement_tasks_by_measure_urn.yml")  # type: ignore
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
@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_get_measure.yml")  # type: ignore
async def test_get_measure(minio_mock: MockMinioClient, client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm_with_system_card("testalgorithm1")])

    # Need to make bucket in object store. The Minio class is mocked by minio_mock.
    storage_client = Minio(
        endpoint=get_settings().OBJECT_STORE_URL,
        access_key=get_settings().OBJECT_STORE_USER,
        secret_key=get_settings().OBJECT_STORE_PASSWORD,
        secure=False,
    )
    storage_client.make_bucket(get_settings().OBJECT_STORE_BUCKET_NAME)

    # when
    response = await client.get("/algorithm/1/measure/urn:nl:ak:mtr:dat-01")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Controleer de datakwaliteit" in response.content


@pytest.mark.asyncio
@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_update_measure_value.yml")  # type: ignore
async def test_update_measure_value(
    minio_mock: MockMinioClient, client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils
) -> None:
    # given
    await db.given([default_user(), default_algorithm_with_system_card("testalgorithm1")])
    client.cookies["fastapi-csrf-token"] = "1"
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    mocker.patch("amt.api.routes.algorithm.get_user_id_or_error", return_value=default_user().id)

    # Need to make bucket in object store. The Minio class is mocked by minio_mock.
    storage_client = Minio(
        endpoint=get_settings().OBJECT_STORE_URL,
        access_key=get_settings().OBJECT_STORE_USER,
        secret_key=get_settings().OBJECT_STORE_PASSWORD,
        secure=False,
    )
    storage_client.make_bucket(get_settings().OBJECT_STORE_BUCKET_NAME)

    # happy flow
    response = await client.post(
        "/algorithm/1/measure/urn:nl:ak:mtr:dat-01",
        data={
            "measure_state": "done",
            "measure_value": "something",
            "measure_links": [],
            "existing_file_names": [],
            "measure_files": [],
        },
        headers={"X-CSRF-Token": "1"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/test_update_measure_value_with_people.yml")  # type: ignore
async def test_update_measure_value_with_people(
    minio_mock: MockMinioClient, client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils
) -> None:
    # given
    await db.given([default_user(), default_algorithm_with_system_card("testalgorithm1")])
    client.cookies["fastapi-csrf-token"] = "1"
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    mocker.patch("amt.api.routes.algorithm.get_user_id_or_error", return_value=default_user().id)

    # Need to make bucket in object store. The Minio class is mocked by minio_mock.
    storage_client = Minio(
        endpoint=get_settings().OBJECT_STORE_URL,
        access_key=get_settings().OBJECT_STORE_USER,
        secret_key=get_settings().OBJECT_STORE_PASSWORD,
        secure=False,
    )
    storage_client.make_bucket(get_settings().OBJECT_STORE_BUCKET_NAME)

    # happy flow
    response = await client.post(
        "/algorithm/1/measure/urn:nl:ak:mtr:dat-01",
        data={
            "measure_state": "done",
            "measure_value": "something",
            "measure_links": [],
            "existing_file_names": [],
            "measure_files": [],
            "measure_responsible": "Default User",
            "measure_accountable": "Default User",
            "measure_reviewer": "Default User",
        },
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
    response = await client.get("/algorithm/1/download")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/yaml; charset=utf-8"


@pytest.mark.asyncio
async def test_get_file(
    minio_mock: MockMinioClient, client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils
) -> None:
    # given
    await db.given([default_user(), default_algorithm_with_system_card("testalgorithm1")])
    client.cookies["fastapi-csrf-token"] = "1"
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    # Need to make bucket in object store. The Minio class is mocked by minio_mock.
    storage_client = Minio(
        endpoint=get_settings().OBJECT_STORE_URL,
        access_key=get_settings().OBJECT_STORE_USER,
        secret_key=get_settings().OBJECT_STORE_PASSWORD,
        secure=False,
    )
    storage_client.make_bucket(get_settings().OBJECT_STORE_BUCKET_NAME)

    file_content = b"test file content"
    file = UploadFile(filename="test.txt", file=BytesIO(file_content))
    file.size = len(file_content)

    object_storage_service = create_object_storage_service()
    path = object_storage_service.upload_file("1", "1", "1", "1", file)
    ulid = path.split("/")[-1]

    # happy flow
    response = await client.get(f"/algorithm/1/file/{ulid}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"


@pytest.mark.asyncio
async def test_delete_file(
    minio_mock: MockMinioClient, client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils
) -> None:
    # given
    await db.given([default_user(), default_algorithm_with_system_card("testalgorithm1")])
    client.cookies["fastapi-csrf-token"] = "1"
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    # Need to make bucket in object store. The Minio class is mocked by minio_mock.
    storage_client = Minio(
        endpoint=get_settings().OBJECT_STORE_URL,
        access_key=get_settings().OBJECT_STORE_USER,
        secret_key=get_settings().OBJECT_STORE_PASSWORD,
        secure=False,
    )
    storage_client.make_bucket(get_settings().OBJECT_STORE_BUCKET_NAME)

    # Mock UploadFile and upload it to Minio and retrieve the ULID.
    file_content = b"test file content"
    file = UploadFile(filename="test.txt", file=BytesIO(file_content))
    file.size = len(file_content)
    object_storage_service = create_object_storage_service()
    path = object_storage_service.upload_file("1", "1", "1", "1", file)
    ulid = path.split("/")[-1]

    # Mock a MeasureTask with file refering to the UploadFile
    mock_get_measure_task_or_error = mocker.patch("amt.api.routes.algorithm.get_measure_task_or_error")
    mock_get_measure_task_or_error.return_value = MeasureTask(
        urn="1", version="1", files=[f"uploads/org/1/algorithm/1/{ulid}"]
    )

    # happy flow
    response = await client.delete(f"/algorithm/1/file/{ulid}", headers={"X-CSRF-Token": "1"})

    assert response.status_code == 200


@pytest.mark.asyncio
def test_get_user_id_or_error_success(mocker: MockFixture) -> None:
    mock_get_user = mocker.patch("amt.api.routes.algorithm.get_user")
    mock_get_user.return_value = {"sub": "user_uuid"}

    assert get_user_id_or_error(MockRequest(lang="nl")) == "user_uuid"


@pytest.mark.asyncio
def test_get_user_id_or_error_failure(mocker: MockFixture) -> None:
    mock_get_user = mocker.patch("amt.api.routes.algorithm.get_user")
    mock_get_user.return_value = None

    with pytest.raises(AMTError):
        get_user_id_or_error(MockRequest(lang="nl"))


@pytest.mark.asyncio
async def test_redirect_to(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_algorithm()])

    response = await client.get("/algorithm/1/redirect?to=/test/path")

    assert response.status_code == 302
    assert response.headers["location"] == "/test/path"


@pytest.mark.asyncio
async def test_resolve_and_enrich_measures(mocker: MockFixture) -> None:
    users_service = UsersService(
        repository=mocker.AsyncMock(spec=UsersRepository),
    )
    users_service.repository.find_by_id.return_value = default_user()  # pyright: ignore[reportFunctionMemberAccess]
    urns = {"urn:nl:ak:mtr:dat-01"}
    my_algorithm = default_algorithm_with_system_card()
    result = await resolve_and_enrich_measures(my_algorithm, urns, users_service)
    assert (
        result["urn:nl:ak:mtr:dat-01"].description
        == "Stel vast of de gebruikte data van voldoende kwaliteit is voor de beoogde toepassing.\n"
    )
    assert len(result["urn:nl:ak:mtr:dat-01"].users) == 3
