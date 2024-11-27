import pytest
from amt.api.lifecycles import Lifecycles
from amt.core.exceptions import AMTNotFound
from amt.models.algorithm import Algorithm
from amt.repositories.algorithms import AlgorithmsRepository
from amt.repositories.organizations import OrganizationsRepository
from amt.schema.algorithm import AlgorithmNew
from amt.schema.system_card import SystemCard
from amt.services.algorithms import AlgorithmsService
from amt.services.instruments import InstrumentsService
from pytest_mock import MockFixture
from tests.constants import default_instrument, default_organization, default_user


@pytest.mark.asyncio
async def test_get_algorithm(mocker: MockFixture):
    # Given
    algorithm_id = 1
    algorithm_name = "Algorithm 1"
    algorithm_lifecycle = "development"
    algorithms_service = AlgorithmsService(
        repository=mocker.AsyncMock(spec=AlgorithmsRepository),
        instrument_service=mocker.AsyncMock(spec=InstrumentsService),
        organizations_repository=mocker.AsyncMock(spec=OrganizationsRepository),
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


@pytest.mark.asyncio
async def test_create_algorithm(mocker: MockFixture):
    algorithm_id = 1
    algorithm_name = "Algorithm 1"
    algorithm_lifecycle = "development"
    system_card = SystemCard(name=algorithm_name)

    organizations_repository = mocker.AsyncMock(spec=OrganizationsRepository)

    algorithms_service = AlgorithmsService(
        repository=mocker.AsyncMock(spec=AlgorithmsRepository),
        instrument_service=mocker.AsyncMock(spec=InstrumentsService),
        organizations_repository=organizations_repository,
    )
    algorithms_service.repository.save.return_value = Algorithm(  # type: ignore
        id=algorithm_id, name=algorithm_name, lifecycle=algorithm_lifecycle, system_card=system_card
    )
    algorithms_service.instrument_service.fetch_instruments.return_value = [default_instrument()]  # type: ignore

    organizations_repository.find_by_id_and_user_id.return_value = default_organization()

    # When
    algorithm_new = AlgorithmNew(
        name=algorithm_name,
        lifecycle=algorithm_lifecycle,
        instruments=[],
        type="algorithm_type",
        open_source="algorithm_open_source",
        publication_category="algorithm_publication_category",
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
        publication_category="algorithm_publication_category",
        systemic_risk="algorithm_systemic_risk",
        transparency_obligations="algorithm_transparency_obligations",
        role="algorithm_role",
        organization_id=1,
    )

    organizations_repository = mocker.AsyncMock(spec=OrganizationsRepository)

    algorithms_service = AlgorithmsService(
        repository=mocker.AsyncMock(spec=AlgorithmsRepository),
        instrument_service=mocker.AsyncMock(spec=InstrumentsService),
        organizations_repository=organizations_repository,
    )

    with pytest.raises(AMTNotFound):
        await algorithms_service.create(algorithm_new, default_user().id)
