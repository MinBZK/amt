import pytest
from amt.core.exceptions import AMTRepositoryError
from amt.repositories.projects import ProjectsRepository
from tests.constants import default_project
from tests.database_test_utils import DatabaseTestUtils


def test_find_all(db: DatabaseTestUtils):
    db.given([default_project(), default_project()])
    project_repository = ProjectsRepository(db.get_session())
    results = project_repository.find_all()
    assert results[0].id == 1
    assert results[1].id == 2
    assert len(results) == 2


def test_find_all_no_results(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    results = project_repository.find_all()
    assert len(results) == 0


def test_save(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    project = default_project()
    project_repository.save(project)

    result = project_repository.find_by_id(1)

    project_repository.delete(project)  # cleanup

    assert result.id == 1
    assert result.name == default_project().name


def test_delete(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    project = default_project()
    project_repository.save(project)
    project_repository.delete(project)

    results = project_repository.find_all()

    assert len(results) == 0


def test_save_failed(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    project = default_project()
    project.id = 1
    project_duplicate = default_project()
    project_duplicate.id = 1

    project_repository.save(project)

    with pytest.raises(AMTRepositoryError):
        project_repository.save(project_duplicate)

    project_repository.delete(project)  # cleanup


def test_delete_failed(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    project = default_project()

    with pytest.raises(AMTRepositoryError):
        project_repository.delete(project)


def test_find_by_id(db: DatabaseTestUtils):
    db.given([default_project()])
    project_repository = ProjectsRepository(db.get_session())
    result = project_repository.find_by_id(1)
    assert result.id == 1
    assert result.name == default_project().name


def test_find_by_id_failed(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    with pytest.raises(AMTRepositoryError):
        project_repository.find_by_id(1)


def test_paginate(db: DatabaseTestUtils):
    db.given([default_project()])
    project_repository = ProjectsRepository(db.get_session())

    result = project_repository.paginate(skip=0, limit=3, search="")

    assert len(result) == 1


def test_paginate_more(db: DatabaseTestUtils):
    db.given([default_project(), default_project(), default_project(), default_project()])
    project_repository = ProjectsRepository(db.get_session())

    result = project_repository.paginate(skip=0, limit=3, search="")

    assert len(result) == 3


def test_paginate_capitalize(db: DatabaseTestUtils):
    db.given(
        [
            default_project(name="Project1"),
            default_project(name="bbb"),
            default_project(name="Aaa"),
            default_project(name="aba"),
        ]
    )
    project_repository = ProjectsRepository(db.get_session())

    result = project_repository.paginate(skip=0, limit=4, search="")

    assert len(result) == 4
    assert result[0].name == "Aaa"
    assert result[1].name == "aba"
    assert result[2].name == "bbb"
    assert result[3].name == "Project1"


def test_search(db: DatabaseTestUtils):
    db.given(
        [
            default_project(name="Project1"),
            default_project(name="bbb"),
            default_project(name="Aaa"),
            default_project(name="aba"),
        ]
    )
    project_repository = ProjectsRepository(db.get_session())

    result = project_repository.paginate(skip=0, limit=4, search="bbb")

    assert len(result) == 1
    assert result[0].name == "bbb"


def test_search_multiple(db: DatabaseTestUtils):
    db.given(
        [
            default_project(name="Project1"),
            default_project(name="bbb"),
            default_project(name="Aaa"),
            default_project(name="aba"),
        ]
    )
    project_repository = ProjectsRepository(db.get_session())

    result = project_repository.paginate(skip=0, limit=4, search="A")

    assert len(result) == 2
    assert result[0].name == "Aaa"
    assert result[1].name == "aba"


def test_search_no_results(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    result = project_repository.paginate(skip=0, limit=4, search="A")
    assert len(result) == 0


def test_raises_exception(db: DatabaseTestUtils):
    db.given([default_project()])
    project_repository = ProjectsRepository(db.get_session())

    with pytest.raises(AMTRepositoryError):
        project_repository.paginate(skip="a", limit=3, search="")  # type: ignore
