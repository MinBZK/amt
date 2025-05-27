from uuid import UUID

import pytest
from amt.models import Authorization
from httpx import AsyncClient
from pytest_mock import MockFixture

from tests.constants import (
    default_algorithm,
    default_auth_user,
    default_authorization,
    default_organization,
    default_user,
)
from tests.database_test_utils import DatabaseTestUtils


@pytest.mark.asyncio
async def test_organizations_get_root(client: AsyncClient) -> None:
    response = await client.get("/organizations/")

    assert response.status_code == 200
    assert b'<div id="organization-search-results"' in response.content


@pytest.mark.asyncio
async def test_organizations_get_root_missing_slash(client: AsyncClient) -> None:
    response = await client.get("/organizations", follow_redirects=True)

    assert response.status_code == 200
    assert b'<div id="organization-search-results"' in response.content


@pytest.mark.asyncio
async def test_organizations_get_root_htmx(client: AsyncClient) -> None:
    response = await client.get("/organizations/", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert b'<table id="organizations-results-table" class="rvo-table margin-top-large">' not in response.content


@pytest.mark.asyncio
@pytest.mark.skip(reason="skipped because the filter is not added because it should not be (user) removable")
async def test_organizations_get_root_htmx_with_group_by(client: AsyncClient) -> None:
    response = await client.get(
        "/organizations/?skip=0&search=&add-filter-organization-type=MY_ORGANIZATIONS", headers={"HX-Request": "true"}
    )

    assert response.status_code == 200
    assert b"/organizations/?skip=0&drop-filter-=organization-type" in response.content


@pytest.mark.asyncio
async def test_organizations_get_search(client: AsyncClient) -> None:
    response = await client.get("/organizations/?skip=0&search=test", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert b'<input type="hidden" name="search" value="test">' in response.content


@pytest.mark.asyncio
async def test_get_new_organizations(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user()])
    await db.init_authorizations_and_roles()

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())

    # when
    response = await client.get("/organizations/new")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"

    assert b'id="form-organization">' in response.content


@pytest.mark.asyncio
async def test_post_new_organizations_bad_request(client: AsyncClient, mocker: MockFixture) -> None:
    # given
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())

    # when
    client.cookies["fastapi-csrf-token"] = "1"
    response = await client.post("/organizations/new", json={}, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 400
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Field required" in response.content


@pytest.mark.asyncio
async def test_post_new_organizations(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()

    client.cookies["fastapi-csrf-token"] = "1"
    new_organization = {
        "name": "test-name",
        "slug": "test-slug",
        "authorization": [{"user_id": default_auth_user()["sub"], "role_id": 1, "type": "Organization"}],
    }
    # given
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())

    # when
    response = await client.post("/organizations/new", json=new_organization, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["HX-Redirect"] == "/organizations/test-slug/members"


@pytest.mark.asyncio
async def test_edit_organization_inline(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()

    client.cookies["fastapi-csrf-token"] = "1"

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())

    # when
    response = await client.get("/organizations/default-organization/edit?full_resource_path=organization/1/name")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert (
        b'hx-put="/organizations/default-organization/update?full_resource_path=organization/1/name"'
        in response.content
    )


@pytest.mark.asyncio
async def test_edit_organization_inline_cancel(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()

    client.cookies["fastapi-csrf-token"] = "1"

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())

    # when
    response = await client.get("/organizations/default-organization/cancel?full_resource_path=organization/1/name")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Edit" in response.content


@pytest.mark.asyncio
async def test_organization_slug(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()

    client.cookies["fastapi-csrf-token"] = "1"

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())

    # when
    response = await client.get("/organizations/default-organization")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_update_organization_inline(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()
    client.cookies["fastapi-csrf-token"] = "1"

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    client.cookies["fastapi-csrf-token"] = "1"
    response = await client.put(
        "/organizations/default-organization/update?full_resource_path=organization/1/name",
        json={"name": "New name"},
        headers={"X-CSRF-Token": "1"},
    )

    assert b"New name" in response.content


@pytest.mark.asyncio
async def test_get_users(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()
    client.cookies["fastapi-csrf-token"] = "1"

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    # when
    response = await client.get("/organizations/users?query=Default")
    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert b'{"value":"92714be3-f798-4461-ba83-55d6cfd889a6","display_value":"Default User"}' in response.content

    # when
    response = await client.get("/organizations/users?query=Default&returnType=search_select_field")
    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b'<span style="padding-inline-start: 1em">Default User</span>' in response.content

    # when
    response = await client.get("/organizations/users?query=D")
    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert b"[]" in response.content


@pytest.mark.asyncio
async def test_get_members(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()
    client.cookies["fastapi-csrf-token"] = "1"

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    # when
    response = await client.get("/organizations/default-organization/members")
    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"/organizations/default-organization/members/92714be3-f798-4461-ba83-55d6cfd889a6" in response.content

    # when
    response = await client.get("/organizations/default-organization/members", headers={"HX-Request": "true"})
    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"/organizations/default-organization/members/92714be3-f798-4461-ba83-55d6cfd889a6" in response.content


@pytest.mark.asyncio
async def test_delete_member(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()
    # add 2nd maintainer member
    user_id = "4738b1e151dc46219556a5662b26517c"
    await db.given([default_user(id=user_id, name="Test User")])
    await db.given([default_authorization(user_id=user_id)])

    client.cookies["fastapi-csrf-token"] = "1"

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    # when
    response = await client.delete(
        f"/organizations/default-organization/members/{default_user().id!s}", headers={"X-CSRF-Token": "1"}
    )

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["HX-Redirect"] == "/organizations/default-organization/members"


@pytest.mark.asyncio
async def test_add_member(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given(
        [
            default_user(),
            default_organization(),
        ]
    )
    await db.init_authorizations_and_roles()
    user_id = "4738b1e151dc46219556a5662b26517c"
    await db.given([default_user(id=user_id, name="Test User")])

    client.cookies["fastapi-csrf-token"] = "1"

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    client.cookies["fastapi-csrf-token"] = "1"
    response = await client.put(
        "/organizations/default-organization/members",
        json={
            "authorization": [
                {"user_id": user_id, "role_id": 1, "type": "Organization", "type_id": default_organization().id}
            ]
        },
        headers={"X-CSRF-Token": "1"},
    )
    authorization: Authorization = (await db.get(Authorization, "user_id", UUID(user_id)))[0]  # pyright: ignore[reportArgumentType]
    assert authorization
    assert authorization.type == "Organization"
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["HX-Redirect"] == "/organizations/default-organization/members"


@pytest.mark.asyncio
async def test_get_algorithms(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given(
        [
            default_user(),
            default_organization(),
            default_algorithm(name="Algorithm1"),
            default_algorithm(name="Algorithm2", organization_id=1),
        ]
    )
    await db.init_authorizations_and_roles()
    client.cookies["fastapi-csrf-token"] = "1"

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())
    mocker.patch("amt.middleware.csrf.CookieOnlyCsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    # when
    response = await client.get("/organizations/default-organization/algorithms")
    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Algorithm1" in response.content
    assert b"Algorithm2" in response.content

    # when
    response = await client.get("/organizations/default-organization/algorithms?search=Algorithm1")
    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Algorithm1" in response.content
    assert b"Algorithm2" not in response.content

    # when
    query = "?skip=5&search=&add-filter-lifecycle=&add-filter-risk-group=VERBODEN_AI&display_type"
    response = await client.get("/organizations/default-organization/algorithms" + query)
    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Algorithm1" not in response.content
    assert b"Algorithm2" not in response.content
