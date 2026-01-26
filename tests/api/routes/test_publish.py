import datetime

import pytest
from amt.api.routes.publish import (
    get_global_steps,
    get_organization_name,
    get_publication_url,
    set_step_state,
    set_steps_completed_until,
)
from amt.core.internationalization import get_translation
from amt.models import Publication
from amt.schema.algoritmeregister import AlgoritmeregisterCredentials, OrganisationOption
from httpx import AsyncClient
from pytest_mock import MockerFixture

from tests.constants import (
    default_algorithm,
    default_organization,
    default_user,
)
from tests.database_test_utils import DatabaseTestUtils


def mock_credentials_with_organisations() -> AlgoritmeregisterCredentials:
    return AlgoritmeregisterCredentials(
        username="test@example.com",
        password="testpassword",  # noqa: S106
        organization_id="org123",
        token="test_token",  # noqa: S106
        organisations=[
            OrganisationOption(value="org123", label="Test Organisation"),
            OrganisationOption(value="org456", label="Another Organisation"),
        ],
    )


def mock_credentials() -> AlgoritmeregisterCredentials:
    return AlgoritmeregisterCredentials(
        username="test@example.com",
        password="testpassword",  # noqa: S106
        organization_id="org123",
        token="test_token",  # noqa: S106
    )


@pytest.mark.asyncio
async def test_publish_router_redirects_to_explanation_when_no_publication(
    client: AsyncClient, db: DatabaseTestUtils
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()

    # when
    response = await client.get("/algorithm/1/publish", follow_redirects=False)

    # then
    assert response.status_code == 302
    assert response.headers["location"] == "/algorithm/1/publish/explanation"


@pytest.mark.asyncio
async def test_publication_explanation_renders_page(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()

    # when
    response = await client.get("/algorithm/1/publish/explanation")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_publish_connection_renders_page(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()

    # when
    response = await client.get("/algorithm/1/publish/connection")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_publish_prepare_redirects_without_credentials(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()

    # when
    response = await client.get("/algorithm/1/publish/prepare", follow_redirects=False)

    # then
    assert response.status_code == 302
    assert response.headers["location"] == "/algorithm/1/publish/connection"


@pytest.mark.asyncio
async def test_publish_preview_redirects_without_credentials(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()

    # when
    response = await client.get("/algorithm/1/publish/preview", follow_redirects=False)

    # then
    assert response.status_code == 302
    assert response.headers["location"] == "/algorithm/1/publish/connection"


@pytest.mark.asyncio
async def test_publish_confirm_redirects_without_credentials(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()

    # when
    response = await client.get("/algorithm/1/publish/confirm", follow_redirects=False)

    # then
    assert response.status_code == 302
    assert response.headers["location"] == "/algorithm/1/publish/connection"


@pytest.mark.asyncio
async def test_publish_send_redirects_without_credentials(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()

    # when
    response = await client.get("/algorithm/1/publish/send", follow_redirects=False)

    # then
    assert response.status_code == 302
    assert response.headers["location"] == "/algorithm/1/publish/connection"


@pytest.mark.asyncio
async def test_publish_status_redirects_without_credentials(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()

    # when
    response = await client.get("/algorithm/1/publish/status", follow_redirects=False)

    # then
    assert response.status_code == 302
    assert response.headers["location"] == "/algorithm/1/publish/connection"


@pytest.mark.asyncio
async def test_ar_login_validation_error_returns_form_with_errors(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    client.cookies["fastapi-csrf-token"] = "1"

    # when
    response = await client.post(
        "/algorithm/1/publish/login",
        json={"username": "", "password": ""},
        headers={"X-CSRF-Token": "1"},
    )

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_ar_login_auth_error_returns_form_with_login_error(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    from amt.algoritmeregister.auth import AlgoritmeregisterAuthError

    mocker.patch(
        "amt.api.routes.publish.get_access_token",
        side_effect=AlgoritmeregisterAuthError,
    )
    client.cookies["fastapi-csrf-token"] = "1"

    # when
    response = await client.post(
        "/algorithm/1/publish/login",
        json={"username": "test@example.com", "password": "wrongpassword"},
        headers={"X-CSRF-Token": "1"},
    )

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_ar_login_success_stores_credentials(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    mocker.patch("amt.api.routes.publish.get_access_token", return_value="test_access_token")

    from amt.algoritmeregister.openapi.base.models import Flow, GetOrganisationsResponse, OrganisationConfig, OrgType

    mock_org_response = GetOrganisationsResponse(
        organisations=[
            OrganisationConfig(
                id=1,
                name="Test Org",
                code="org123",
                org_id="1",
                type=OrgType.GEMEENTE,
                flow=Flow.ICTU_LAST,
                show_page=True,
            )
        ],
        count=1,
    )
    mock_org_api = mocker.Mock()
    mock_org_api.get_all.return_value = mock_org_response
    mocker.patch("amt.api.routes.publish.OrganisationApi", return_value=mock_org_api)

    client.cookies["fastapi-csrf-token"] = "1"

    # when
    response = await client.post(
        "/algorithm/1/publish/login",
        json={"username": "test@example.com", "password": "testpassword"},
        headers={"X-CSRF-Token": "1"},
    )

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_publish_without_permission_returns_404(client: AsyncClient, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])

    # when
    response = await client.get("/algorithm/1/publish/explanation")

    # then
    assert response.status_code == 404


def test_get_global_steps() -> None:
    # given
    translations = get_translation("en")

    # when
    steps = get_global_steps(translations)

    # then
    assert len(steps) == 5
    assert steps[0]["state"] == "start"
    assert steps[0]["label"] == "Start"
    assert steps[4]["state"] == "end"


def test_set_step_state() -> None:
    # given
    translations = get_translation("en")
    steps = get_global_steps(translations)

    # when
    set_step_state(steps, "./prepare", "doing")

    # then
    assert steps[1]["state"] == "doing"


def test_set_step_state_not_found() -> None:
    # given
    translations = get_translation("en")
    steps = get_global_steps(translations)

    # when
    set_step_state(steps, "./nonexistent", "doing")

    # then (no change)
    assert all(s["state"] != "doing" for s in steps)


def test_set_steps_completed_until() -> None:
    # given
    translations = get_translation("en")
    steps = get_global_steps(translations)

    # when
    set_steps_completed_until(steps, "./preview")

    # then
    assert steps[0]["state"] == "start"  # unchanged
    assert steps[1]["state"] == "completed"
    assert steps[2]["state"] == "doing"
    assert steps[3]["state"] == "incomplete"


def test_get_publication_url() -> None:
    # when
    result = get_publication_url("ORG", "LARS123", "My Test Algorithm")

    # then
    assert "ORG" in result
    assert "LARS123" in result
    assert "my-test-algorithm" in result


def test_get_publication_url_removes_special_characters() -> None:
    # when
    result = get_publication_url("ORG", "LARS123", "Test & Algorithm (v2)")

    # then
    assert "test--algorithm-v2" in result


@pytest.mark.asyncio
async def test_publish_prepare_renders_with_credentials(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=mock_credentials())

    # when
    response = await client.get("/algorithm/1/publish/prepare")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_publish_preview_renders_with_credentials(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=mock_credentials())

    # when
    response = await client.get("/algorithm/1/publish/preview")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_publish_confirm_renders_with_credentials(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=mock_credentials())

    # when
    response = await client.get("/algorithm/1/publish/confirm")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_publish_status_renders_with_credentials_no_publication(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=mock_credentials())

    # when
    response = await client.get("/algorithm/1/publish/status")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_publish_status_renders_with_credentials_and_publication_published(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    publication = Publication(
        last_updated=datetime.datetime.now(tz=None),  # noqa: DTZ005
        algorithm_id=1,
        lars="LARS123",
        organization_code="RIG",
    )
    await db.given([publication])
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=mock_credentials())

    mock_summary = mocker.Mock()
    mock_summary.published = True
    mock_summary.current_version_released = False
    mocker.patch("amt.api.routes.publish.get_algorithms_status", return_value=[mock_summary])

    # when
    response = await client.get("/algorithm/1/publish/status")

    # then
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_publish_status_renders_with_credentials_and_publication_state_2(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    publication = Publication(
        last_updated=datetime.datetime.now(tz=None),  # noqa: DTZ005
        algorithm_id=1,
        lars="LARS456",
        organization_code="RIG",
    )
    await db.given([publication])
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=mock_credentials())

    mock_summary = mocker.Mock()
    mock_summary.published = False
    mock_summary.current_version_released = True
    mocker.patch("amt.api.routes.publish.get_algorithms_status", return_value=[mock_summary])

    # when
    response = await client.get("/algorithm/1/publish/status")

    # then
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_publish_status_renders_with_credentials_and_publication_state_1(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    publication = Publication(
        last_updated=datetime.datetime.now(tz=None),  # noqa: DTZ005
        algorithm_id=1,
        lars="LARS789",
        organization_code="RIG",
    )
    await db.given([publication])
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=mock_credentials())

    mock_summary = mocker.Mock()
    mock_summary.published = False
    mock_summary.current_version_released = False
    mocker.patch("amt.api.routes.publish.get_algorithms_status", return_value=[mock_summary])

    # when
    response = await client.get("/algorithm/1/publish/status")

    # then
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_publish_send_creates_new_publication(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=mock_credentials())

    mock_result = mocker.Mock()
    mock_result.lars_code = "NEW_LARS"
    mocker.patch("amt.api.routes.publish.publish_algorithm", return_value=mock_result)

    # when
    response = await client.get("/algorithm/1/publish/send", follow_redirects=False)

    # then
    assert response.status_code == 200  # Redirect template response


@pytest.mark.asyncio
async def test_publish_send_updates_existing_publication(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    publication = Publication(
        last_updated=datetime.datetime.now(tz=None),  # noqa: DTZ005
        algorithm_id=1,
        lars="11111111",
        organization_code="RIG",
    )
    await db.given([publication])
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=mock_credentials())

    mock_result = mocker.Mock()
    mock_result.lars_code = "11111111"
    mocker.patch("amt.api.routes.publish.update_algorithm", return_value=mock_result)

    # when
    response = await client.get("/algorithm/1/publish/send", follow_redirects=False)

    # then
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_publish_release(client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    publication = Publication(
        last_updated=datetime.datetime.now(tz=None),  # noqa: DTZ005
        algorithm_id=1,
        lars="22222222",
        organization_code="RIG",
    )
    await db.given([publication])
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=mock_credentials())
    mocker.patch("amt.api.routes.publish.release_algorithm", return_value=None)

    # when
    response = await client.get("/algorithm/1/release/22222222", follow_redirects=False)

    # then
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_publish_release_no_credentials_redirects(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=None)

    # when
    response = await client.get("/algorithm/1/release/LARS123", follow_redirects=False)

    # then
    assert response.status_code == 302
    assert response.headers["location"] == "/algorithm/1/publish/connection"


@pytest.mark.asyncio
async def test_publish_release_no_publication_raises_not_found(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=mock_credentials())

    # when
    response = await client.get("/algorithm/1/release/NONEXISTENT")

    # then
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_preview_with_credentials(client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    publication = Publication(
        last_updated=datetime.datetime.now(tz=None),  # noqa: DTZ005
        algorithm_id=1,
        lars="33333333",
        organization_code="RIG",
    )
    await db.given([publication])
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=mock_credentials())

    mock_preview = mocker.Mock()
    mock_preview.preview_url = "https://preview.example.com/test"
    mocker.patch("amt.api.routes.publish.preview_algorithm", return_value=mock_preview)

    # when
    response = await client.get("/algorithm/1/preview/33333333", follow_redirects=False)

    # then
    assert response.status_code == 307
    assert response.headers["location"] == "https://preview.example.com/test"


@pytest.mark.asyncio
async def test_preview_no_credentials_redirects(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=None)

    # when
    response = await client.get("/algorithm/1/preview/LARS123", follow_redirects=False)

    # then
    assert response.status_code == 302
    assert response.headers["location"] == "/algorithm/1/publish/connection"


@pytest.mark.asyncio
async def test_preview_no_publication_raises_not_found(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.core.session_utils.get_algoritmeregister_credentials", return_value=mock_credentials())

    # when
    response = await client.get("/algorithm/1/preview/NONEXISTENT")

    # then
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_publish_router_redirects_to_step_when_in_progress(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    from amt.core.session_utils import PublishStep

    mocker.patch("amt.api.routes.publish.get_publish_step", return_value=PublishStep.PREPARE)

    # when
    response = await client.get("/algorithm/1/publish", follow_redirects=False)

    # then
    assert response.status_code == 302
    assert response.headers["location"] == "/algorithm/1/publish/prepare"


@pytest.mark.asyncio
async def test_publish_router_redirects_to_status_when_publication_exists(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    publication = Publication(
        last_updated=datetime.datetime.now(tz=None),  # noqa: DTZ005
        algorithm_id=1,
        lars="LARS123",
        organization_code="RIG",
    )
    await db.given([publication])
    mocker.patch("amt.api.routes.publish.get_publish_step", return_value=None)

    # when
    response = await client.get("/algorithm/1/publish", follow_redirects=False)

    # then
    assert response.status_code == 302
    assert response.headers["location"] == "/algorithm/1/publish/status"


def test_get_organization_name_returns_label_from_organisations_list() -> None:
    # given
    credentials = mock_credentials_with_organisations()

    # when
    result = get_organization_name(credentials)

    # then
    assert result == "Test Organisation"


def test_get_organization_name_returns_organization_id_as_fallback() -> None:
    # given
    credentials = AlgoritmeregisterCredentials(
        username="test@example.com",
        password="testpassword",  # noqa: S106
        organization_id="unknown_org",
        token="test_token",  # noqa: S106
        organisations=[],
    )

    # when
    result = get_organization_name(credentials)

    # then
    assert result == "unknown_org"


def test_get_organization_name_returns_none_when_no_organization_id() -> None:
    # given
    credentials = AlgoritmeregisterCredentials(
        username="test@example.com",
        password="testpassword",  # noqa: S106
        organization_id=None,
        token="test_token",  # noqa: S106
    )

    # when
    result = get_organization_name(credentials)

    # then
    assert result is None


@pytest.mark.asyncio
async def test_set_organization_with_select_preserves_organisations_list(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    credentials = mock_credentials_with_organisations()
    credentials.organization_id = None
    mocker.patch("amt.api.routes.publish.get_algoritmeregister_credentials", return_value=credentials)
    store_mock = mocker.patch("amt.api.routes.publish.store_algoritmeregister_credentials")
    client.cookies["fastapi-csrf-token"] = "1"

    # when
    response = await client.post(
        "/algorithm/1/publish/set-organization",
        json={"organization_id": "org456"},
        headers={"X-CSRF-Token": "1"},
        follow_redirects=False,
    )

    # then
    assert response.status_code == 200
    store_mock.assert_called_once()
    stored_credentials = store_mock.call_args[0][1]
    assert stored_credentials.organization_id == "org456"
    assert len(stored_credentials.organisations) == 2
    assert stored_credentials.organisations[0].value == "org123"
    assert stored_credentials.organisations[1].value == "org456"


@pytest.mark.asyncio
async def test_set_organization_with_manual_entry_stores_organization_name(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    credentials = AlgoritmeregisterCredentials(
        username="test@example.com",
        password="testpassword",  # noqa: S106
        organization_id=None,
        token="test_token",  # noqa: S106
        organisations=[],
    )
    mocker.patch("amt.api.routes.publish.get_algoritmeregister_credentials", return_value=credentials)
    store_mock = mocker.patch("amt.api.routes.publish.store_algoritmeregister_credentials")
    client.cookies["fastapi-csrf-token"] = "1"

    # when
    response = await client.post(
        "/algorithm/1/publish/set-organization",
        json={"organization_id": "manual_org", "organization_name": "Manual Organisation Name"},
        headers={"X-CSRF-Token": "1"},
        follow_redirects=False,
    )

    # then
    assert response.status_code == 200
    store_mock.assert_called_once()
    stored_credentials = store_mock.call_args[0][1]
    assert stored_credentials.organization_id == "manual_org"
    assert len(stored_credentials.organisations) == 1
    assert stored_credentials.organisations[0].value == "manual_org"
    assert stored_credentials.organisations[0].label == "Manual Organisation Name"


@pytest.mark.asyncio
async def test_set_organization_validation_error_for_empty_organization_id(
    client: AsyncClient, db: DatabaseTestUtils, mocker: MockerFixture
) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("testalgorithm1")])
    await db.init_authorizations_and_roles()
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    mocker.patch("amt.api.routes.publish.get_algoritmeregister_credentials", return_value=mock_credentials())
    client.cookies["fastapi-csrf-token"] = "1"

    # when
    response = await client.post(
        "/algorithm/1/publish/set-organization",
        json={"organization_id": ""},
        headers={"X-CSRF-Token": "1"},
    )

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
