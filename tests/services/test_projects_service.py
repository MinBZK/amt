from unittest.mock import Mock

from amt.models.project import Project
from amt.repositories.projects import ProjectsRepository
from amt.schema.project import ProjectNew
from amt.schema.system_card import SystemCard
from amt.services.instruments import InstrumentsService
from amt.services.projects import ProjectsService
from amt.services.tasks import TasksService
from tests.constants import default_instrument


def test_get_project():
    # Given
    project_id = 1
    project_name = "Project 1"
    project_lifecycle = "development"
    projects_service = ProjectsService(
        repository=Mock(spec=ProjectsRepository),
        task_service=Mock(spec=TasksService),
        instrument_service=Mock(spec=InstrumentsService),
    )
    projects_service.repository.find_by_id.return_value = Project(  # type: ignore
        id=project_id, name=project_name, lifecycle=project_lifecycle
    )

    # When
    project = projects_service.get(project_id)

    # Then
    assert project.id == project_id
    assert project.name == project_name
    assert project.lifecycle == project_lifecycle
    projects_service.repository.find_by_id.assert_called_once_with(project_id)  # type: ignore


def test_create_project():
    project_id = 1
    project_name = "Project 1"
    project_lifecycle = "development"
    system_card = SystemCard(name=project_name)

    projects_service = ProjectsService(
        repository=Mock(spec=ProjectsRepository),
        task_service=Mock(spec=TasksService),
        instrument_service=Mock(spec=InstrumentsService),
    )
    projects_service.repository.save.return_value = Project(  # type: ignore
        id=project_id, name=project_name, lifecycle=project_lifecycle, system_card=system_card
    )
    projects_service.instrument_service.fetch_instruments.return_value = [default_instrument()]  # type: ignore

    # When
    project_new = ProjectNew(
        name=project_name,
        lifecycle=project_lifecycle,
        instruments=[],
        type="project_type",
        open_source="project_open_source",
        publication_category="project_publication_category",
        systemic_risk="project_systemic_risk",
        transparency_obligations="project_transparency_obligations",
        role="project_role",
    )
    project = projects_service.create(project_new)

    # Then
    assert project.id == project_id
    assert project.name == project_name
    assert project.lifecycle == project_lifecycle
    projects_service.repository.save.assert_called()  # type: ignore
