from collections.abc import MutableMapping
from datetime import UTC, datetime
from typing import Any, cast

import pytest
from amt.api.routes.shared import get_localized_value
from amt.models import Algorithm
from amt.models.base import Base
from amt.schema.ai_act_profile import AiActProfile
from amt.schema.algorithm import AlgorithmNew
from amt.schema.system_card import SystemCard
from amt.services.task_registry import get_requirements_and_measures
from fastapi.requests import Request
from httpx import AsyncClient
from pytest_mock import MockFixture
from starlette.datastructures import URL

from tests.constants import default_algorithm, default_auth_user, default_instrument, default_user
from tests.database_test_utils import DatabaseTestUtils


@pytest.mark.asyncio
async def test_algorithms_get_root(client: AsyncClient) -> None:
    response = await client.get("/algorithms/")

    assert response.status_code == 200
    assert b'<div id="algorithm-search-results"' in response.content


@pytest.mark.asyncio
async def test_algorithms_get_root_missing_slash(client: AsyncClient) -> None:
    response = await client.get("/algorithms", follow_redirects=True)

    assert response.status_code == 200
    assert b'<div id="algorithm-search-results"' in response.content


@pytest.mark.asyncio
async def test_algorithms_get_root_htmx(client: AsyncClient) -> None:
    response = await client.get("/algorithms/", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert b'<table id="search-results-table" class="rvo-table margin-top-large">' not in response.content


@pytest.mark.asyncio
async def test_algorithms_get_root_htmx_with_group_by(client: AsyncClient) -> None:
    response = await client.get("/algorithms/?skip=0&display_type=LIFECYCLE", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert b'<table id="search-results-table" class="rvo-table margin-top-large">' not in response.content


@pytest.mark.asyncio
async def test_algorithms_get_root_htmx_with_group_by_and_lifecycle_filter(client: AsyncClient) -> None:
    response = await client.get(
        "/algorithms/?skip=0&add-filter-lifecycle=DESIGN&display_type=LIFECYCLE", headers={"HX-Request": "true"}
    )

    assert response.status_code == 200
    assert b'<table id="search-results-table" class="rvo-table margin-top-large">' not in response.content


@pytest.mark.asyncio
async def test_algorithms_get_root_htmx_with_algorithms_mock(client: AsyncClient, mocker: MockFixture) -> None:
    mock_algorithm = default_algorithm()
    mock_algorithm.last_edited = datetime.now(UTC)
    # given
    mocker.patch("amt.services.algorithms.AlgorithmsService.paginate", return_value=[mock_algorithm])

    # when
    response = await client.get("/algorithms/", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert b'<table id="search-results-table" class="rvo-table margin-top-large">' in response.content


@pytest.mark.asyncio
async def test_get_new_algorithms(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user()])

    mocker.patch(
        "amt.services.instruments.InstrumentsService.fetch_instruments",
        return_value=[default_instrument(urn="urn1", name="name1"), default_instrument(urn="urn2", name="name2")],
    )
    mocker.patch("amt.api.routes.algorithms.get_user", return_value=default_auth_user())

    # when
    response = await client.get("/algorithms/new")
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
async def test_post_new_algorithms_bad_request(client: AsyncClient, mocker: MockFixture) -> None:
    # given
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    mocker.patch("amt.core.authorization.get_user", return_value=default_auth_user())

    # when
    client.cookies["fastapi-csrf-token"] = "1"
    response = await client.post("/algorithms/new", json={}, headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 400
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"Field required" in response.content


@pytest.mark.asyncio
async def test_post_new_algorithms(client: AsyncClient, mocker: MockFixture, db: DatabaseTestUtils) -> None:
    await db.given([default_user()])

    client.cookies["fastapi-csrf-token"] = "1"
    new_algorithm = AlgorithmNew(
        name="default algorithm",
        lifecycle="DESIGN",
        type="AI-systeem",
        open_source="open-source",
        risk_group="hoog-risico AI",
        conformity_assessment_body="beoordeling door derde partij",
        systemic_risk="geen systeemrisico",
        transparency_obligations="geen transparantieverplichting",
        role="gebruiksverantwoordelijke",
        template_id="0",
        organization_id=1,
    )
    # given
    mocker.patch("fastapi_csrf_protect.CsrfProtect.validate_csrf", new_callable=mocker.AsyncMock)
    mocker.patch(
        "amt.services.instruments.InstrumentsService.fetch_instruments",
        return_value=[default_instrument(urn="urn1", name="name1"), default_instrument(urn="urn2", name="name2")],
    )
    mocker.patch("amt.api.routes.algorithms.get_user", return_value=default_auth_user())

    # when
    response = await client.post("/algorithms/new", json=new_algorithm.model_dump(), headers={"X-CSRF-Token": "1"})

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["HX-Redirect"] == "/algorithm/1/details/tasks"


@pytest.mark.asyncio
async def test_post_new_algorithms_write_system_card(
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
    mocker.patch("amt.api.routes.algorithms.get_user", return_value=default_auth_user())

    await db.given([default_user()])

    name = "name1"
    algorithm_new = AlgorithmNew(
        name=name,
        lifecycle="DESIGN",
        type="AI-systeem",
        open_source="open-source",
        risk_group="hoog-risico AI",
        conformity_assessment_body="beoordeling door derde partij",
        systemic_risk="geen systeemrisico",
        transparency_obligations="geen transparantieverplichting",
        role="gebruiksverantwoordelijke",
        template_id="",
        organization_id=1,
    )

    ai_act_profile = AiActProfile(
        type=algorithm_new.type,
        open_source=algorithm_new.open_source,
        risk_group=algorithm_new.risk_group,
        conformity_assessment_body=algorithm_new.conformity_assessment_body,
        systemic_risk=algorithm_new.systemic_risk,
        transparency_obligations=algorithm_new.transparency_obligations,
        role=algorithm_new.role,
    )

    requirements, measures = await get_requirements_and_measures(ai_act_profile)

    system_card = SystemCard(
        name=algorithm_new.name,
        instruments=[],
        ai_act_profile=ai_act_profile,
        requirements=requirements,
        measures=measures,
    )

    # when
    await client.post("/algorithms/new", json=algorithm_new.model_dump(), headers={"X-CSRF-Token": "1"})

    # then
    base_algorithms: list[Base] = await db.get(Algorithm, "name", name)
    algorithms: list[Algorithm] = cast(list[Algorithm], base_algorithms)
    assert any(algorithm.system_card == system_card for algorithm in algorithms if algorithm.system_card is not None)


class MockRequest(Request):
    def __init__(self, lang: str, scope: MutableMapping[str, Any] | None = None, url: str | None = None) -> None:
        if scope is None:
            scope = {}
        if url:
            self._url = URL(url=url)
        self.lang = lang
        self.scope = scope

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
    localized = get_localized_value("risk-group", "HOOG_RISICO_AI", request)
    assert localized.display_value == "Hoog-risico AI"

    request = MockRequest("en")
    localized = get_localized_value("risk-group", "HOOG_RISICO_AI", request)
    assert localized.display_value == "high-risk AI"

    request = MockRequest("en")
    localized = get_localized_value("other key", "", request)
    assert localized.display_value == "Unknown filter option"
