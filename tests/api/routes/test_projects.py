from collections.abc import Generator
from typing import cast
from unittest.mock import Mock

import pytest
from amt.api.routes.projects import get_localized_value
from amt.models import Project
from amt.models.base import Base
from amt.schema.ai_act_profile import AiActProfile
from amt.schema.project import ProjectNew
from amt.schema.system_card import SystemCard
from amt.services.instruments import InstrumentsService
from amt.services.task_registry import get_requirements_and_measures
from fastapi.requests import Request
from fastapi.testclient import TestClient
from fastapi_csrf_protect import CsrfProtect  # type: ignore # noqa

from tests.constants import default_instrument
from tests.database_test_utils import DatabaseTestUtils


@pytest.fixture
def init_instruments() -> Generator[None, None, None]:  # noqa: PT004
    origin = InstrumentsService.fetch_instruments
    InstrumentsService.fetch_instruments = Mock(
        return_value=[default_instrument(urn="urn1", name="name1"), default_instrument(urn="urn2", name="name2")]
    )
    yield
    InstrumentsService.fetch_instruments = origin


def test_projects_get_root(client: TestClient) -> None:
    response = client.get("/algorithm-systems/")

    assert response.status_code == 200
    assert b'<div id="project-search-results">' in response.content


def test_projects_get_root_missing_slash(client: TestClient) -> None:
    response = client.get("/algorithm-systems")

    assert response.status_code == 200
    assert b'<div id="project-search-results">' in response.content


def test_projects_get_root_htmx(client: TestClient) -> None:
    response = client.get("/algorithm-systems/", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert b'<table id="search-results-table" class="rvo-table margin-top-large">' not in response.content


def test_get_new_projects(client: TestClient, init_instruments: Generator[None, None, None]) -> None:
    # when
    response = client.get("/algorithm-systems/new")
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


def test_post_new_projects_bad_request(client: TestClient, mocker) -> None:
    # given
    CsrfProtect.validate_csrf = mocker.AsyncMock()

    # when
    client.cookies["fastapi-csrf-token"] = "1"
    response = client.post("/algorithm-systems/new", json={}, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 400
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"name: Field required" in response.content


def test_post_new_projects(
    client: TestClient, mocker, init_instruments: Generator[None, None, None]
) -> None:
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
    CsrfProtect.validate_csrf = mocker.AsyncMock()

    # when
    response = client.post("/algorithm-systems/new", json=new_project.model_dump(), headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["HX-Redirect"] == "/algorithm-system/1/details/tasks"


def test_post_new_projects_write_system_card(
    client: TestClient,
    mocker,
    init_instruments: Generator[None, None, None],
    db: DatabaseTestUtils,
) -> None:
    # Given
    client.cookies["fastapi-csrf-token"] = "1"
    CsrfProtect.validate_csrf = mocker.AsyncMock()

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
    client.post("/algorithm-systems/new", json=project_new.model_dump(), headers={"X-CSRF-Token": "1"})

    # then
    base_projects: list[Base] = db.get(Project, "name", name)
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
