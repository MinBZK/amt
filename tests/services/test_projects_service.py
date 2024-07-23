from pathlib import Path
from unittest.mock import Mock

from amt.models.project import Project
from amt.repositories.projects import ProjectsRepository
from amt.schema.project import ProjectNew
from amt.services.instruments import InstrumentsService
from amt.services.projects import ProjectsService
from amt.services.tasks import TasksService
from tests.constants import default_instrument


def test_get_project():
    # Given
    project_id = 1
    project_name = "Project 1"
    project_model_card = "model_card_path"
    projects_service = ProjectsService(
        repository=Mock(spec=ProjectsRepository),
        task_service=Mock(spec=TasksService),
        instrument_service=Mock(spec=InstrumentsService),
    )
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
    project_id = 1
    project_name = "Project 1"
    project_model_card = Path("model_card_path")
    projects_service = ProjectsService(
        repository=Mock(spec=ProjectsRepository),
        task_service=Mock(spec=TasksService),
        instrument_service=Mock(spec=InstrumentsService),
    )
    projects_service.repository.save.return_value = Project(  # type: ignore
        id=project_id, name=project_name, model_card=str(project_model_card)
    )
    projects_service.instrument_service.fetch_instruments.return_value = [default_instrument()]  # type: ignore

    # When
    project_new = ProjectNew(name=project_name, instruments=[])
    project = projects_service.create(project_new)

    # Then
    assert project.id == project_id
    assert project.name == project_name
    projects_service.repository.save.assert_called()  # type: ignore
