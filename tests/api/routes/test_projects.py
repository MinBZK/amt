from datetime import UTC, datetime
from typing import cast

import pytest
from amt.api.routes.projects import get_localized_value
from amt.models import Project
from amt.models.base import Base
from amt.schema.ai_act_profile import AiActProfile
from amt.schema.project import ProjectNew
from amt.schema.system_card import SystemCard
from amt.services.task_registry import get_requirements_and_measures
from fastapi.requests import Request
from httpx import AsyncClient
from pytest_mock import MockFixture

from tests.constants import default_instrument, default_project
from tests.database_test_utils import DatabaseTestUtils


@pytest.mark.asyncio
async def test_projects_get_root(client: AsyncClient) -> None:
    response = await client.get("/algorithm-systems/")

    assert response.status_code == 200
    assert b'<div id="project-search-results"' in response.content


@pytest.mark.asyncio
async def test_projects_get_root_missing_slash(client: AsyncClient) -> None:
    response = await client.get("/algorithm-systems", follow_redirects=True)

    assert response.status_code == 200
    assert b'<div id="project-search-results"' in response.content


@pytest.mark.asyncio
async def test_projects_get_root_htmx(client: AsyncClient) -> None:
    response = await client.get("/algorithm-systems/", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert b'<table id="search-results-table" class="rvo-table margin-top-large">' not in response.content


@pytest.mark.asyncio
async def test_projects_get_root_htmx_with_group_by(client: AsyncClient) -> None:
    response = await client.get("/algorithm-systems/?skip=0&display_type=LIFECYCLE", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert b'<table id="search-results-table" class="rvo-table margin-top-large">' not in response.content


@pytest.mark.asyncio
async def test_projects_get_root_htmx_with_group_by_and_lifecycle_filter(client: AsyncClient) -> None:
    response = await client.get(
        "/algorithm-systems/?skip=0&add-filter-lifecycle=DESIGN&display_type=LIFECYCLE", headers={"HX-Request": "true"}
    )

    assert response.status_code == 200
    assert b'<table id="search-results-table" class="rvo-table margin-top-large">' not in response.content


@pytest.mark.asyncio
async def test_projects_get_root_htmx_with_projects_mock(client: AsyncClient, mocker: MockFixture) -> None:
    mock_project = default_project()
    mock_project.last_edited = datetime.now(UTC)
    # given
    mocker.patch("amt.services.projects.ProjectsService.paginate", return_value=[mock_project])

    # when
    response = await client.get("/algorithm-systems/", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert b'<table id="search-results-table" class="rvo-table margin-top-large">' in response.content


@pytest.mark.asyncio
async def test_get_new_projects(client: AsyncClient, mocker: MockFixture) -> None:
    # given
    mocker.patch(
        "amt.services.instruments.InstrumentsService.fetch_instruments",
        return_value=[default_instrument(urn="urn1", name="name1"), default_instrument(urn="urn2", name="name2")],
    )

    # when
    response = await client.get("/algorithm-systems/new")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    content = " ".join(response.content.decode().split())

    assert (
        '<input id="urn1" name="instruments" class="rvo-checkbox__input" type="checkbox" value="urn1" /> name1'
        in content
    )
    assert (
        '<input id="urn2" name="instruments" class="rvo-checkbox__input" type="checkbox" value="urn2" /> name2'
        in content
    )


@pytest.mark.asyncio
async def test_post_new_projects_bad_request(client: AsyncClient, mocker: MockFixture) -> None:
    # given
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)

    # when
    client.cookies["fastapi-csrf-token"] = "1"
    response = await client.post("/algorithm-systems/new", json={}, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 400
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Field required" in response.content


@pytest.mark.asyncio
async def test_post_new_projects(client: AsyncClient, mocker: MockFixture) -> None:
    client.cookies["fastapi-csrf-token"] = "1"
    new_project = ProjectNew(
        name="default project",
        lifecycle="DESIGN",
        type="AI-systeem",
        open_source="open-source",
        publication_category="hoog-risico AI",
        systemic_risk="geen systeemrisico",
        transparency_obligations="geen transparantieverplichtingen",
        role="gebruiksverantwoordelijke",
    )
    # given
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    mocker.patch(
        "amt.services.instruments.InstrumentsService.fetch_instruments",
        return_value=[default_instrument(urn="urn1", name="name1"), default_instrument(urn="urn2", name="name2")],
    )

    # when
    response = await client.post("/algorithm-systems/new", json=new_project.model_dump(), headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["HX-Redirect"] == "/algorithm-system/1/details/tasks"


@pytest.mark.asyncio
async def test_post_new_projects_write_system_card(
    client: AsyncClient,
    mocker: MockFixture,
    db: DatabaseTestUtils,
) -> None:
    # Given
    client.cookies["fastapi-csrf-token"] = "1"
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    mocker.patch(
        "amt.services.instruments.InstrumentsService.fetch_instruments",
        return_value=[default_instrument(urn="urn1", name="name1"), default_instrument(urn="urn2", name="name2")],
    )

    name = "name1"
    project_new = ProjectNew(
        name=name,
        lifecycle="DESIGN",
        type="AI-systeem",
        open_source="open-source",
        publication_category="hoog-risico AI",
        systemic_risk="geen systeemrisico",
        transparency_obligations="geen transparantieverplichtingen",
        role="gebruiksverantwoordelijke",
    )

    ai_act_profile = AiActProfile(
        type=project_new.type,
        open_source=project_new.open_source,
        publication_category=project_new.publication_category,
        systemic_risk=project_new.systemic_risk,
        transparency_obligations=project_new.transparency_obligations,
        role=project_new.role,
    )

    # This should be refactored; this is here because for the demo of 18 oct the requirements and
    # measures are hardcoded
    requirements, measures = get_requirements_and_measures(ai_act_profile)

    system_card = SystemCard(
        name=project_new.name,
        instruments=[],
        ai_act_profile=ai_act_profile,
        requirements=requirements,
        measures=measures,
    )

    # when
    await client.post("/algorithm-systems/new", json=project_new.model_dump(), headers={"X-CSRF-Token": "1"})

    # then
    base_projects: list[Base] = await db.get(Project, "name", name)
    projects: list[Project] = cast(list[Project], base_projects)
    assert any(project.system_card == system_card for project in projects if project.system_card is not None)


class MockRequest(Request):
    def __init__(self, lang: str) -> None:
        self.lang = lang

    @property
    def headers(self):  # type: ignore
        return {"Accept-Language": self.lang}


def test_get_localized_value():
    request = MockRequest("nl")
    localized = get_localized_value("lifecycle", "PROBLEM_ANALYSIS", request)
    assert localized.display_value == "Probleemanalyse"

    request = MockRequest("en")
    localized = get_localized_value("lifecycle", "PROBLEM_ANALYSIS", request)
    assert localized.display_value == "Problem Analysis"

    request = MockRequest("nl")
    localized = get_localized_value("publication-category", "HOOG_RISICO_AI", request)
    assert localized.display_value == "Hoog-risico AI"

    request = MockRequest("en")
    localized = get_localized_value("publication-category", "HOOG_RISICO_AI", request)
    assert localized.display_value == "High-risk AI"

    request = MockRequest("en")
    localized = get_localized_value("other key", "", request)
    assert localized.display_value == "Unknown filter option"
