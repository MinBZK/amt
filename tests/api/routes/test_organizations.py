import pytest
from amt.schema.organization import OrganizationNew
from httpx import AsyncClient
from pytest_mock import MockFixture

from tests.constants import default_auth_user, default_user
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

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())

    # when
    response = await client.get("/organizations/new")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"

    assert b'id="form-organization">' in response.content


@pytest.mark.asyncio
async def test_post_new_organizations_bad_request(client: AsyncClient, mocker: MockFixture) -> None:
    # given
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
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
    await db.given([default_user()])

    client.cookies["fastapi-csrf-token"] = "1"
    new_organization = OrganizationNew(name="test-name", slug="test-slug", user_ids=[default_auth_user()["sub"]])
    # given
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())

    # when
    response = await client.post(
        "/organizations/new", json=new_organization.model_dump(), headers={"X-CSRF-Token": "1"}
    )

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["HX-Redirect"] == "/organizations/test-slug"


@pytest.mark.asyncio
async def test_edit_organization_inline(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user()])

    client.cookies["fastapi-csrf-token"] = "1"

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())

    # when
    response = await client.get("/organizations/default-organization/edit/name?edit_type=systemcard")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"/organizations/default-organization/update/name?edit_type=systemcard" in response.content


@pytest.mark.asyncio
async def test_organization_slug(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user()])

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
    await db.given([default_user()])
    client.cookies["fastapi-csrf-token"] = "1"

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    client.cookies["fastapi-csrf-token"] = "1"
    response = await client.put(
        "/organizations/default-organization/update/name?edit_type=systemcard",
        json={"value": "New name"},
        headers={"X-CSRF-Token": "1"},
    )

    assert b"New name" in response.content


@pytest.mark.asyncio
async def test_get_users(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user()])
    client.cookies["fastapi-csrf-token"] = "1"

    mocker.patch("amt.api.routes.organizations.get_user", return_value=default_auth_user())
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

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