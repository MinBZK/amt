import pytest
from tad.core.exceptions import RepositoryError
from tad.repositories.projects import ProjectsRepository
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

    with pytest.raises(RepositoryError):
        project_repository.save(project_duplicate)

    project_repository.delete(project)  # cleanup


def test_delete_failed(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    project = default_project()

    with pytest.raises(RepositoryError):
        project_repository.delete(project)


def test_find_by_id(db: DatabaseTestUtils):
    db.given([default_project()])
    project_repository = ProjectsRepository(db.get_session())
    result = project_repository.find_by_id(1)
    assert result.id == 1
    assert result.name == default_project().name


def test_find_by_id_failed(db: DatabaseTestUtils):
    project_repository = ProjectsRepository(db.get_session())
    with pytest.raises(RepositoryError):
        project_repository.find_by_id(1)
