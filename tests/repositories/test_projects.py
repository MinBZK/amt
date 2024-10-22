import pytest
from amt.core.exceptions import AMTRepositoryError
from amt.models import Project
from amt.repositories.projects import ProjectsRepository
from tests.constants import default_project
from tests.database_test_utils import DatabaseTestUtils


@pytest.mark.asyncio
async def test_find_all(db: DatabaseTestUtils):
    await db.given([default_project(), default_project()])
    project_repository = ProjectsRepository(db.get_session())
    results = await project_repository.find_all()
    assert results[0].id == 1
    assert results[1].id == 2
    assert len(results) == 2


@pytest.mark.asyncio
async def test_find_all_no_results(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    results = await project_repository.find_all()
    assert len(results) == 0


@pytest.mark.asyncio
async def test_save(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    project = default_project()
    await project_repository.save(project)

    result = await project_repository.find_by_id(1)

    await project_repository.delete(project)  # cleanup

    assert result.id == 1
    assert result.name == default_project().name


@pytest.mark.asyncio
async def test_delete(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    project = default_project()
    await project_repository.save(project)
    await project_repository.delete(project)

    results = await project_repository.find_all()

    assert len(results) == 0


@pytest.mark.asyncio
async def test_save_failed(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    project = default_project()
    project.id = 1
    project_duplicate = default_project()
    project_duplicate.id = 1

    await project_repository.save(project)

    with pytest.raises(AMTRepositoryError):
        await project_repository.save(project_duplicate)

    await project_repository.delete(project)  # cleanup


@pytest.mark.asyncio
async def test_delete_failed(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    project = default_project()

    with pytest.raises(AMTRepositoryError):
        await project_repository.delete(project)


@pytest.mark.asyncio
async def test_find_by_id(db: DatabaseTestUtils):
    await db.given([default_project()])
    project_repository = ProjectsRepository(db.get_session())
    result = await project_repository.find_by_id(1)
    assert result.id == 1
    assert result.name == default_project().name


@pytest.mark.asyncio
async def test_find_by_id_failed(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    with pytest.raises(AMTRepositoryError):
        await project_repository.find_by_id(1)


@pytest.mark.asyncio
async def test_paginate(db: DatabaseTestUtils):
    await db.given([default_project()])
    project_repository = ProjectsRepository(db.get_session())

    result: list[Project] = await project_repository.paginate(skip=0, limit=3, search="", filters={}, sort={})

    assert len(result) == 1


@pytest.mark.asyncio
async def test_paginate_more(db: DatabaseTestUtils):
    await db.given([default_project(), default_project(), default_project(), default_project()])
    project_repository = ProjectsRepository(db.get_session())

    result: list[Project] = await project_repository.paginate(skip=0, limit=3, search="", filters={}, sort={})

    assert len(result) == 3


@pytest.mark.asyncio
async def test_paginate_capitalize(db: DatabaseTestUtils):
    await db.given(
        [
            default_project(name="Project1"),
            default_project(name="bbb"),
            default_project(name="Aaa"),
            default_project(name="aba"),
        ]
    )
    project_repository = ProjectsRepository(db.get_session())

    result: list[Project] = await project_repository.paginate(skip=0, limit=4, search="", filters={}, sort={})

    assert len(result) == 4
    assert result[0].name == "Aaa"
    assert result[1].name == "aba"
    assert result[2].name == "bbb"
    assert result[3].name == "Project1"


@pytest.mark.asyncio
async def test_search(db: DatabaseTestUtils):
    await db.given(
        [
            default_project(name="Project1"),
            default_project(name="bbb"),
            default_project(name="Aaa"),
            default_project(name="aba"),
        ]
    )
    project_repository = ProjectsRepository(db.get_session())

    result: list[Project] = await project_repository.paginate(skip=0, limit=4, search="bbb", filters={}, sort={})

    assert len(result) == 1
    assert result[0].name == "bbb"


@pytest.mark.asyncio
async def test_search_multiple(db: DatabaseTestUtils):
    await db.given(
        [
            default_project(name="Project1"),
            default_project(name="bbb"),
            default_project(name="Aaa"),
            default_project(name="aba"),
        ]
    )
    project_repository = ProjectsRepository(db.get_session())

    result: list[Project] = await project_repository.paginate(skip=0, limit=4, search="A", filters={}, sort={})

    assert len(result) == 2
    assert result[0].name == "Aaa"
    assert result[1].name == "aba"


@pytest.mark.asyncio
async def test_search_no_results(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    result: list[Project] = await project_repository.paginate(skip=0, limit=4, search="A", filters={}, sort={})
    assert len(result) == 0


@pytest.mark.asyncio
async def test_raises_exception(db: DatabaseTestUtils):
    await db.given([default_project()])
    project_repository = ProjectsRepository(db.get_session())

    with pytest.raises(AMTRepositoryError):
        await project_repository.paginate(skip="a", limit=3, search="", filters={}, sort={})  # type: ignore
