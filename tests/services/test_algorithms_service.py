import pytest
from amt.api.lifecycles import Lifecycles
from amt.core.exceptions import AMTNotFound
from amt.models.algorithm import Algorithm
from amt.repositories.algorithms import AlgorithmsRepository
from amt.repositories.organizations import OrganizationsRepository
from amt.repositories.tasks import TasksRepository
from amt.schema.algorithm import AlgorithmNew
from amt.schema.system_card import SystemCard
from amt.services.algorithms import AlgorithmsService
from amt.services.authorization import AuthorizationsService
from pytest_mock import MockFixture
from tests.conftest import amt_vcr
from tests.constants import default_organization, default_user


@pytest.mark.asyncio
async def test_get_algorithm(mocker: MockFixture):
    # Given
    algorithm_id = 1
    algorithm_name = "Algorithm 1"
    algorithm_lifecycle = "development"
    algorithms_service = AlgorithmsService(
        repository=mocker.AsyncMock(spec=AlgorithmsRepository),
        organizations_repository=mocker.AsyncMock(spec=OrganizationsRepository),
        tasks_repository=mocker.AsyncMock(spec=TasksRepository),
        authorizations_service=mocker.AsyncMock(spec=AuthorizationsService),
    )
    algorithms_service.repository.find_by_id.return_value = Algorithm(  # type: ignore
        id=algorithm_id, name=algorithm_name, lifecycle=algorithm_lifecycle
    )

    # When
    algorithm = await algorithms_service.get(algorithm_id)

    # Then
    assert algorithm.id == algorithm_id
    assert algorithm.name == algorithm_name
    assert algorithm.lifecycle == algorithm_lifecycle
    algorithms_service.repository.find_by_id.assert_awaited_once_with(algorithm_id)  # type: ignore


@amt_vcr.use_cassette("tests/fixtures/vcr_cassettes/service_test_create_algorithm.yaml")  # type: ignore
@pytest.mark.asyncio
async def test_create_algorithm(mocker: MockFixture):
    algorithm_id = 1
    algorithm_name = "Algorithm 1"
    algorithm_lifecycle = "development"
    system_card = SystemCard(name=algorithm_name)  # pyright: ignore[reportCallIssue]

    organizations_repository = mocker.AsyncMock(spec=OrganizationsRepository)

    algorithms_service = AlgorithmsService(
        repository=mocker.AsyncMock(spec=AlgorithmsRepository),
        organizations_repository=organizations_repository,
        tasks_repository=mocker.AsyncMock(spec=TasksRepository),
        authorizations_service=mocker.AsyncMock(spec=AuthorizationsService),
    )
    algorithms_service.repository.save.return_value = Algorithm(  # type: ignore
        id=algorithm_id, name=algorithm_name, lifecycle=algorithm_lifecycle, system_card=system_card
    )

    organizations_repository.find_by_id_and_user_id.return_value = default_organization()

    # When
    algorithm_new = AlgorithmNew(
        name=algorithm_name,
        lifecycle=algorithm_lifecycle,
        instruments=[],
        type="algorithm_type",
        open_source="algorithm_open_source",
        risk_group="algorithm_risk_group",
        systemic_risk="algorithm_systemic_risk",
        transparency_obligations="algorithm_transparency_obligations",
        role="algorithm_role",
        organization_id=1,
    )
    algorithm = await algorithms_service.create(algorithm_new, default_user().id)

    # Then
    assert algorithm.id == algorithm_id
    assert algorithm.name == algorithm_name
    assert algorithm.lifecycle == algorithm_lifecycle
    algorithms_service.repository.save.assert_awaited()  # type: ignore


@pytest.mark.asyncio
async def test_create_algorithm_unknown_template_id(mocker: MockFixture):
    # When
    algorithm_new = AlgorithmNew(
        template_id="1",
        name="test",
        lifecycle=Lifecycles.DEVELOPMENT.name,
        instruments=[],
        type="algorithm_type",
        open_source="algorithm_open_source",
        risk_group="algorithm_risk_group",
        systemic_risk="algorithm_systemic_risk",
        transparency_obligations="algorithm_transparency_obligations",
        role="algorithm_role",
        organization_id=1,
    )

    organizations_repository = mocker.AsyncMock(spec=OrganizationsRepository)
    organizations_repository.find_by_id_and_user_id.return_value = default_organization()

    algorithms_service = AlgorithmsService(
        repository=mocker.AsyncMock(spec=AlgorithmsRepository),
        organizations_repository=organizations_repository,
        tasks_repository=mocker.AsyncMock(spec=TasksRepository),
        authorizations_service=mocker.AsyncMock(spec=AuthorizationsService),
    )

    with pytest.raises(AMTNotFound):
        await algorithms_service.create(algorithm_new, default_user().id)
