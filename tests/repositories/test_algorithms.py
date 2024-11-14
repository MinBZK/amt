import pytest
from amt.api.lifecycles import Lifecycles
from amt.api.publication_category import PublicationCategories
from amt.core.exceptions import AMTRepositoryError
from amt.models import Algorithm
from amt.repositories.algorithms import AlgorithmsRepository, sort_by_lifecycle, sort_by_lifecycle_reversed
from tests.constants import default_algorithm, default_algorithm_with_lifecycle, default_algorithm_with_system_card
from tests.database_test_utils import DatabaseTestUtils


@pytest.mark.asyncio
async def test_find_all(db: DatabaseTestUtils):
    await db.given([default_algorithm(), default_algorithm()])
    algorithm_repository = AlgorithmsRepository(db.get_session())
    results = await algorithm_repository.find_all()
    assert results[0].id == 1
    assert results[1].id == 2
    assert len(results) == 2


@pytest.mark.asyncio
async def test_find_all_no_results(db: DatabaseTestUtils):
    algorithm_repository = AlgorithmsRepository(db.get_session())
    results = await algorithm_repository.find_all()
    assert len(results) == 0


@pytest.mark.asyncio
async def test_save(db: DatabaseTestUtils):
    algorithm_repository = AlgorithmsRepository(db.get_session())
    algorithm = default_algorithm()
    await algorithm_repository.save(algorithm)

    result = await algorithm_repository.find_by_id(1)

    await algorithm_repository.delete(algorithm)  # cleanup

    assert result.id == 1
    assert result.name == default_algorithm().name


@pytest.mark.asyncio
async def test_delete(db: DatabaseTestUtils):
    algorithm_repository = AlgorithmsRepository(db.get_session())
    algorithm = default_algorithm()
    await algorithm_repository.save(algorithm)
    await algorithm_repository.delete(algorithm)

    results = await algorithm_repository.find_all()

    assert len(results) == 0


@pytest.mark.asyncio
async def test_save_failed(db: DatabaseTestUtils):
    algorithm_repository = AlgorithmsRepository(db.get_session())
    algorithm = default_algorithm()
    algorithm.id = 1
    algorithm_duplicate = default_algorithm()
    algorithm_duplicate.id = 1

    await algorithm_repository.save(algorithm)

    with pytest.raises(AMTRepositoryError):
        await algorithm_repository.save(algorithm_duplicate)

    await algorithm_repository.delete(algorithm)  # cleanup


@pytest.mark.asyncio
async def test_delete_failed(db: DatabaseTestUtils):
    algorithm_repository = AlgorithmsRepository(db.get_session())
    algorithm = default_algorithm()

    with pytest.raises(AMTRepositoryError):
        await algorithm_repository.delete(algorithm)


@pytest.mark.asyncio
async def test_find_by_id(db: DatabaseTestUtils):
    await db.given([default_algorithm()])
    algorithm_repository = AlgorithmsRepository(db.get_session())
    result = await algorithm_repository.find_by_id(1)
    assert result.id == 1
    assert result.name == default_algorithm().name


@pytest.mark.asyncio
async def test_find_by_id_failed(db: DatabaseTestUtils):
    algorithm_repository = AlgorithmsRepository(db.get_session())
    with pytest.raises(AMTRepositoryError):
        await algorithm_repository.find_by_id(1)


@pytest.mark.asyncio
async def test_paginate(db: DatabaseTestUtils):
    await db.given([default_algorithm()])
    algorithm_repository = AlgorithmsRepository(db.get_session())

    result: list[Algorithm] = await algorithm_repository.paginate(skip=0, limit=3, search="", filters={}, sort={})

    assert len(result) == 1


@pytest.mark.asyncio
async def test_paginate_more(db: DatabaseTestUtils):
    await db.given([default_algorithm(), default_algorithm(), default_algorithm(), default_algorithm()])
    algorithm_repository = AlgorithmsRepository(db.get_session())

    result: list[Algorithm] = await algorithm_repository.paginate(skip=0, limit=3, search="", filters={}, sort={})

    assert len(result) == 3


@pytest.mark.asyncio
async def test_paginate_capitalize(db: DatabaseTestUtils):
    await db.given(
        [
            default_algorithm(name="Algorithm1"),
            default_algorithm(name="bbb"),
            default_algorithm(name="Aaa"),
            default_algorithm(name="aba"),
        ]
    )
    algorithm_repository = AlgorithmsRepository(db.get_session())

    result: list[Algorithm] = await algorithm_repository.paginate(skip=0, limit=4, search="", filters={}, sort={})

    assert len(result) == 4
    assert result[0].name == "Aaa"
    assert result[1].name == "aba"
    assert result[2].name == "Algorithm1"
    assert result[3].name == "bbb"


@pytest.mark.asyncio
async def test_search(db: DatabaseTestUtils):
    await db.given(
        [
            default_algorithm(name="Algorithm1"),
            default_algorithm(name="bbb"),
            default_algorithm(name="Aaa"),
            default_algorithm(name="aba"),
        ]
    )
    algorithm_repository = AlgorithmsRepository(db.get_session())

    result: list[Algorithm] = await algorithm_repository.paginate(skip=0, limit=4, search="bbb", filters={}, sort={})

    assert len(result) == 1
    assert result[0].name == "bbb"


@pytest.mark.asyncio
async def test_search_multiple(db: DatabaseTestUtils):
    await db.given(
        [
            default_algorithm(name="Algorithm1"),
            default_algorithm(name="bbb"),
            default_algorithm(name="Aaa"),
            default_algorithm(name="aba"),
        ]
    )
    algorithm_repository = AlgorithmsRepository(db.get_session())

    result: list[Algorithm] = await algorithm_repository.paginate(skip=0, limit=4, search="A", filters={}, sort={})

    assert len(result) == 3
    assert result[0].name == "Aaa"
    assert result[1].name == "aba"
    assert result[2].name == "Algorithm1"


@pytest.mark.asyncio
async def test_search_no_results(db: DatabaseTestUtils):
    algorithm_repository = AlgorithmsRepository(db.get_session())
    result: list[Algorithm] = await algorithm_repository.paginate(skip=0, limit=4, search="A", filters={}, sort={})
    assert len(result) == 0


@pytest.mark.asyncio
async def test_raises_exception(db: DatabaseTestUtils):
    await db.given([default_algorithm()])
    algorithm_repository = AlgorithmsRepository(db.get_session())

    with pytest.raises(AMTRepositoryError):
        await algorithm_repository.paginate(skip="a", limit=3, search="", filters={}, sort={})  # type: ignore


@pytest.mark.asyncio
async def test_sort_by_lifecyle(db: DatabaseTestUtils):
    await db.given(
        [
            default_algorithm_with_lifecycle(name="Algorithm1", lifecycle=Lifecycles.DESIGN),
            default_algorithm(name="Algorithm2"),
        ]
    )
    algorithm_repository = AlgorithmsRepository(db.get_session())

    algorithms: list[Algorithm] = await algorithm_repository.paginate(skip=0, limit=4, search="", filters={}, sort={})
    result = sort_by_lifecycle(algorithms[0])
    assert result == 2

    result = sort_by_lifecycle(algorithms[1])
    assert result == -1


@pytest.mark.asyncio
async def test_sort_by_lifecycle_reversed(db: DatabaseTestUtils):
    await db.given(
        [
            default_algorithm_with_lifecycle(name="Algorithm1", lifecycle=Lifecycles.DESIGN),
            default_algorithm(name="Algorithm2"),
        ]
    )
    algorithm_repository = AlgorithmsRepository(db.get_session())

    algorithms: list[Algorithm] = await algorithm_repository.paginate(skip=0, limit=4, search="", filters={}, sort={})
    result = sort_by_lifecycle_reversed(algorithms[0])
    assert result == -2

    result = sort_by_lifecycle_reversed(algorithms[1])
    assert result == 1


@pytest.mark.asyncio
async def test_with_lifecycle_filter(db: DatabaseTestUtils):
    await db.given(
        [
            default_algorithm_with_lifecycle(name="Algorithm1"),
            default_algorithm(name="Algorithm2"),
            default_algorithm(name="Algorithm3"),
            default_algorithm(name="Algorithm4"),
        ]
    )
    algorithm_repository = AlgorithmsRepository(db.get_session())

    result: list[Algorithm] = await algorithm_repository.paginate(
        skip=0, limit=4, search="", filters={"lifecycle": Lifecycles.DESIGN.name}, sort={}
    )

    assert len(result) == 1
    assert result[0].name == "Algorithm1"


@pytest.mark.asyncio
async def test_with_publication_category_filter(db: DatabaseTestUtils):
    await db.given(
        [
            default_algorithm_with_system_card(name="Algorithm1"),
            default_algorithm(name="Algorithm2"),
            default_algorithm(name="Algorithm3"),
            default_algorithm(name="Algorithm4"),
        ]
    )
    algorithm_repository = AlgorithmsRepository(db.get_session())

    result: list[Algorithm] = await algorithm_repository.paginate(
        skip=0, limit=4, search="", filters={"publication-category": PublicationCategories.HOOG_RISICO_AI.name}, sort={}
    )

    assert len(result) == 1
    assert result[0].name == "Algorithm1"


@pytest.mark.asyncio
async def test_with_sorting(db: DatabaseTestUtils):
    await db.given(
        [
            default_algorithm_with_lifecycle(name="Algorithm1", lifecycle=Lifecycles.DESIGN),
            default_algorithm_with_lifecycle(name="Algorithm2", lifecycle=Lifecycles.PHASING_OUT),
        ]
    )
    algorithm_repository = AlgorithmsRepository(db.get_session())

    # Sort name Ascending
    result: list[Algorithm] = await algorithm_repository.paginate(
        skip=0, limit=4, search="", filters={}, sort={"name": "ascending"}
    )
    assert result[0].name == "Algorithm1"

    # Sort name Descending
    result: list[Algorithm] = await algorithm_repository.paginate(
        skip=0, limit=4, search="", filters={}, sort={"name": "descending"}
    )
    assert result[0].name == "Algorithm2"

    # Sort last_update Ascending
    result: list[Algorithm] = await algorithm_repository.paginate(
        skip=0, limit=4, search="", filters={}, sort={"last_update": "ascending"}
    )
    assert result[0].name == "Algorithm1"

    # Sort last_update Descending
    result: list[Algorithm] = await algorithm_repository.paginate(
        skip=0, limit=4, search="", filters={}, sort={"last_update": "descending"}
    )
    assert result[0].name == "Algorithm1"

    # Sort lifecycle regular
    result: list[Algorithm] = await algorithm_repository.paginate(
        skip=0, limit=4, search="", filters={}, sort={"lifecycle": "ascending"}
    )
    assert result[0].name == "Algorithm1"

    # Sort lifecycle reversed
    result: list[Algorithm] = await algorithm_repository.paginate(
        skip=0, limit=4, search="", filters={}, sort={"lifecycle": "descending"}
    )
    assert result[0].name == "Algorithm2"
