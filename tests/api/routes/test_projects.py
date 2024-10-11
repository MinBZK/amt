from collections.abc import Generator
from unittest.mock import MagicMock, Mock

import pytest
from amt.schema.ai_act_profile import AiActProfile
from amt.schema.project import ProjectNew
from amt.schema.system_card import SystemCard
from amt.services.instruments import InstrumentsService
from amt.services.storage import FileSystemStorageService
from fastapi.testclient import TestClient
from fastapi_csrf_protect import CsrfProtect  # type: ignore # noqa

from tests.constants import default_instrument


@pytest.fixture
def init_instruments() -> Generator[None, None, None]:  # noqa: PT004
    origin = InstrumentsService.fetch_instruments
    InstrumentsService.fetch_instruments = Mock(
        return_value=[default_instrument(urn="urn1", name="name1"), default_instrument(urn="urn2", name="name2")]
    )
    yield
    InstrumentsService.fetch_instruments = origin


def test_projects_get_root(client: TestClient) -> None:
    response = client.get("/projects/")

    assert response.status_code == 200
    assert b'<ul class="rvo-item-list" id="project-search-results">' in response.content


def test_projects_get_root_missing_slash(client: TestClient) -> None:
    response = client.get("/projects")

    assert response.status_code == 200
    assert b'<ul class="rvo-item-list" id="project-search-results">' in response.content


def test_projects_get_root_htmx(client: TestClient) -> None:
    response = client.get("/projects/", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert b'<ul class="rvo-item-list" id="project-search-results">' not in response.content


def test_get_new_projects(client: TestClient, init_instruments: Generator[None, None, None]) -> None:
    # when
    response = client.get("/projects/new")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"

    assert (
        b'<input id="urn1" name="instruments" class="rvo-checkbox__input" type="checkbox" value="urn1" />name1'
        in response.content
    )
    assert (
        b'<input id="urn2" name="instruments" class="rvo-checkbox__input" type="checkbox" value="urn2" />name2'
        in response.content
    )


def test_post_new_projects_bad_request(client: TestClient, mock_csrf: Generator[None, None, None]) -> None:
    # when
    client.cookies["fastapi-csrf-token"] = "1"
    response = client.post("/projects/new", json={}, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 400
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"name: Field required" in response.content


def test_post_new_projects(
    client: TestClient, mock_csrf: Generator[None, None, None], init_instruments: Generator[None, None, None]
) -> None:
    client.cookies["fastapi-csrf-token"] = "1"
    new_project = ProjectNew(
        name="default project",
        lifecycle="DESIGN",
        type="AI-systeem",
        open_source="open-source",
        publication_category="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichtingen",
        role="aanbieder",
    )

    # when
    response = client.post("/projects/new", json=new_project.model_dump(), headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["HX-Redirect"] == "/project/1/details/tasks"


def test_post_new_projects_write_system_card(
    client: TestClient, mock_csrf: Generator[None, None, None], init_instruments: Generator[None, None, None]
) -> None:
    # Given
    client.cookies["fastapi-csrf-token"] = "1"
    origin = FileSystemStorageService.write
    FileSystemStorageService.write = MagicMock()
    project_new = ProjectNew(
        name="name1",
        lifecycle="DESIGN",
        type="AI-systeem",
        open_source="open-source",
        publication_category="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichtingen",
        role="aanbieder",
    )

    ai_act_profile = AiActProfile(
        type=project_new.type,
        open_source=project_new.open_source,
        publication_category=project_new.publication_category,
        systemic_risk=project_new.systemic_risk,
        transparency_obligations=project_new.transparency_obligations,
        role=project_new.role,
    )

    system_card = SystemCard(name=project_new.name, instruments=[], ai_act_profile=ai_act_profile)

    # when
    client.post("/projects/new", json=project_new.model_dump(), headers={"X-CSRF-Token": "1"})

    # then
    FileSystemStorageService.write.assert_called_with(system_card.model_dump())
    FileSystemStorageService.write = origin
