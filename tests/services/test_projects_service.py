from pathlib import Path
from unittest.mock import Mock

from tad.models.project import Project
from tad.repositories.projects import ProjectsRepository
from tad.schema.project import ProjectNew
from tad.services.projects import ProjectsService


def test_get_project():
    # Given
    project_id = 1
    project_name = "Project 1"
    project_model_card = "model_card_path"
    projects_service = ProjectsService(repository=Mock(spec=ProjectsRepository))
    projects_service.repository.find_by_id.return_value = Project(  # type: ignore
        id=project_id, name=project_name, model_card=project_model_card
    )

    # When
    project = projects_service.get(project_id)

    if project is None:
        raise AssertionError()

    # Then
    assert project.id == project_id
    assert project.name == project_name
    assert project.model_card == project_model_card
    projects_service.repository.find_by_id.assert_called_once_with(project_id)  # type: ignore


def test_create_project():
    # Given
    project_id = 1
    project_name = "Project 1"
    project_model_card = Path("model_card_path")
    projects_service = ProjectsService(repository=Mock(spec=ProjectsRepository))
    projects_service.repository.save.return_value = Project(  # type: ignore
        id=project_id, name=project_name, model_card=str(project_model_card)
    )

    # When
    project_new = ProjectNew(name=project_name, instruments=[])
    project = projects_service.create(project_new)

    # Then
    assert project.id == project_id
    assert project.name == project_name
    projects_service.repository.save.assert_called()  # type: ignore
