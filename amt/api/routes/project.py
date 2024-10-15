import functools
import logging
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from amt.api.deps import templates
from amt.api.lifecycles import get_lifecycle
from amt.api.navigation import (
    BaseNavigationItem,
    Navigation,
    NavigationItem,
    resolve_base_navigation_items,
    resolve_navigation_items,
)
from amt.core.exceptions import AMTNotFound, AMTRepositoryError
from amt.enums.status import Status
from amt.models import Project
from amt.schema.system_card import SystemCard
from amt.schema.task import MovedTask
from amt.services.instruments_and_requirements_state import InstrumentStateService, RequirementsStateService
from amt.services.projects import ProjectsService
from amt.services.storage import StorageFactory
from amt.services.task_registry import fetch_measures, fetch_requirements
from amt.services.tasks import TasksService
from amt.utils.storage import get_include_content

router = APIRouter()
logger = logging.getLogger(__name__)


def get_system_card_data() -> SystemCard:
    # TODO: This now loads an example system card independent of the project ID.
    path = Path("example_system_card/system_card.yaml")
    system_card: Any = StorageFactory.init(storage_type="file", location=path.parent, filename=path.name).read()
    return SystemCard(**system_card)


@functools.lru_cache
def get_instrument_state() -> dict[str, Any]:
    system_card_data = get_system_card_data()
    instrument_state = InstrumentStateService(system_card_data)
    instrument_states = instrument_state.get_state_per_instrument()
    return {
        "instrument_states": instrument_states,
        "count_0": instrument_state.get_amount_completed_instruments(),
        "count_1": instrument_state.get_amount_total_instruments(),
    }


def get_requirements_state(system_card: SystemCard) -> dict[str, Any]:
    requirements = fetch_requirements([requirement.urn for requirement in system_card.requirements])
    requirements_state_service = RequirementsStateService(system_card)
    requirements_state = requirements_state_service.get_requirements_state(requirements)

    return {
        "states": requirements_state,
        "count_0": requirements_state_service.get_amount_completed_requirements(),
        "count_1": requirements_state_service.get_amount_total_requirements(),
    }


def get_project_or_error(project_id: int, projects_service: ProjectsService, request: Request) -> Project:
    try:
        logger.debug(f"getting project with id {project_id}")
        project = projects_service.get(project_id)
        request.state.path_variables = {"project_id": project_id}
    except AMTRepositoryError as e:
        raise AMTNotFound from e
    return project


def get_project_details_tabs(request: Request) -> list[NavigationItem]:
    return resolve_navigation_items(
        [
            Navigation.PROJECT_SYSTEM_INFO,
            Navigation.PROJECT_SYSTEM_ALGORITHM_DETAILS,
            Navigation.PROJECT_MODEL,
            Navigation.PROJECT_REQUIREMENTS,
            Navigation.PROJECT_DATA_CARD,
            Navigation.PROJECT_TASKS,
            Navigation.PROJECT_SYSTEM_INSTRUMENTS,
        ],
        request,
    )


def get_projects_submenu_items() -> list[BaseNavigationItem]:
    return [
        Navigation.PROJECTS_OVERVIEW,
        Navigation.PROJECT_TASKS,
        Navigation.PROJECT_SYSTEM_CARD,
    ]


@router.get("/{project_id}/details/tasks")
async def get_tasks(
    request: Request,
    project_id: int,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
    tasks_service: Annotated[TasksService, Depends(TasksService)],
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)
    tab_items = get_project_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/details/system_card"),
            Navigation.PROJECT_TASKS,
        ],
        request,
    )

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "tasks_service": tasks_service,
        "statuses": Status,
        "project": project,
        "project_id": project.id,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
    }

    return templates.TemplateResponse(request, "projects/tasks.html.j2", context)


@router.patch("/move_task")
async def move_task(
    request: Request,
    moved_task: MovedTask,
    tasks_service: Annotated[TasksService, Depends(TasksService)],
) -> HTMLResponse:
    """
    Move a task through an API call.
    :param tasks_service: the task service
    :param request: the request object
    :param moved_task: the move task object
    :return: a HTMLResponse object, in this case the html code of the card that was moved
    """
    # because htmx form always sends a value and siblings are optional, we use -1 for None and convert it here
    if moved_task.next_sibling_id == -1:
        moved_task.next_sibling_id = None
    if moved_task.previous_sibling_id == -1:
        moved_task.previous_sibling_id = None
    task = tasks_service.move_task(
        moved_task.id,
        moved_task.status_id,
        moved_task.previous_sibling_id,
        moved_task.next_sibling_id,
    )

    context = {"task": task}

    return templates.TemplateResponse(request, "parts/task.html.j2", context=context)


@router.get("/{project_id}/details")
async def get_project_details(
    request: Request, project_id: int, projects_service: Annotated[ProjectsService, Depends(ProjectsService)]
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/details/system_card"),
            Navigation.PROJECT_DETAILS,
        ],
        request,
    )

    system_card_data = get_system_card_data()
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)

    tab_items = get_project_details_tabs(request)

    context = {
        "lifecycle": get_lifecycle(project.lifecycle, request),
        "last_edited": project.last_edited,
        "system_card": system_card_data,
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "project": project,
        "project_id": project.id,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
    }

    return templates.TemplateResponse(request, "projects/details_info.html.j2", context)


# !!!
# Implementation of this endpoint is for now independent of the project ID, meaning
# that the same system card is rendered for all project ID's. This is due to the fact
# that the logical process flow of a system card is not complete.
# !!!
@router.get("/{project_id}/details/system_card")
async def get_system_card(
    request: Request,
    project_id: int,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)

    tab_items = get_project_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/details/system_card"),
            Navigation.PROJECT_SYSTEM_CARD,
        ],
        request,
    )

    # TODO: This now loads an example system card independent of the project ID.
    filepath = Path("example_system_card/system_card.yaml")
    file_system_storage_service = StorageFactory.init(
        storage_type="file", location=filepath.parent, filename=filepath.name
    )
    system_card_data = file_system_storage_service.read()

    context = {
        "system_card": system_card_data,
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "last_edited": project.last_edited,
        "project": project,
        "project_id": project.id,
        "tab_items": tab_items,
        "breadcrumbs": breadcrumbs,
    }

    return templates.TemplateResponse(request, "pages/system_card.html.j2", context)


@router.get("/{project_id}/details/model/inference")
async def get_project_inference(
    request: Request, project_id: int, projects_service: Annotated[ProjectsService, Depends(ProjectsService)]
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/details/model/inference"),
            Navigation.PROJECT_MODEL,
        ],
        request,
    )

    system_card_data = get_system_card_data()
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)

    tab_items = get_project_details_tabs(request)

    context = {
        "lifecycle": get_lifecycle(project.lifecycle, request),
        "last_edited": project.last_edited,
        "system_card": system_card_data,
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "project": project,
        "project_id": project.id,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
    }

    return templates.TemplateResponse(request, "projects/details_inference.html.j2", context)


# !!!
# Implementation of this endpoint is for now independent of the project ID, meaning
# that the same system card is rendered for all project ID's. This is due to the fact
# that the logical process flow of a system card is not complete.
# !!!
@router.get("/{project_id}/details/system_card/requirements")
async def get_system_card_requirements(
    request: Request,
    project_id: int,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)
    # TODO: This tab is fairly slow, fix in later releases
    tab_items = get_project_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/details/system_card"),
            Navigation.PROJECT_SYSTEM_CARD,
        ],
        request,
    )

    # TODO: This is only for the demo of 18 Oct. In reality one would load the requirements from the requirement
    # field in the system card, but one would load the AI Act Profile and determine the requirements from
    # the labels in this field.
    system_card = project.system_card
    requirements = fetch_requirements([requirement.urn for requirement in system_card.requirements])

    # Get measures that correspond to the requirements.
    requirements_and_measures = [(requirement, fetch_measures(requirement.links)) for requirement in requirements]

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "project": project,
        "project_id": project.id,
        "tab_items": tab_items,
        "breadcrumbs": breadcrumbs,
        "requirements_and_measures": requirements_and_measures,
    }

    return templates.TemplateResponse(request, "projects/details_requirements.html.j2", context)


# !!!
# Implementation of this endpoint is for now independent of the project ID, meaning
# that the same system card is rendered for all project ID's. This is due to the fact
# that the logical process flow of a system card is not complete.
# !!!
@router.get("/{project_id}/details/system_card/data")
async def get_system_card_data_page(
    request: Request,
    project_id: int,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)

    tab_items = get_project_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/details/system_card"),
            Navigation.PROJECT_SYSTEM_CARD,
        ],
        request,
    )

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "project": project,
        "project_id": project.id,
        "tab_items": tab_items,
        "breadcrumbs": breadcrumbs,
    }

    return templates.TemplateResponse(request, "projects/details_data.html.j2", context)


# !!!
# Implementation of this endpoint is for now independent of the project ID, meaning
# that the same system card is rendered for all project ID's. This is due to the fact
# that the logical process flow of a system card is not complete.
# !!!
@router.get("/{project_id}/details/system_card/instruments")
async def get_system_card_instruments(
    request: Request,
    project_id: int,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)

    tab_items = get_project_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/details/system_card"),
            Navigation.PROJECT_SYSTEM_CARD,
        ],
        request,
    )

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "project": project,
        "project_id": project.id,
        "tab_items": tab_items,
        "breadcrumbs": breadcrumbs,
    }

    return templates.TemplateResponse(request, "projects/details_instruments.html.j2", context)


# !!!
# Implementation of this endpoint is for now independent of the project ID, meaning
# that the same system card is rendered for all project ID's. This is due to the fact
# that the logical process flow of a system card is not complete.
# !!!
@router.get("/{project_id}/details/system_card/assessments/{assessment_card}")
async def get_assessment_card(
    request: Request,
    project_id: int,
    assessment_card: str,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)

    request.state.path_variables.update({"assessment_card": assessment_card})

    sub_menu_items = resolve_navigation_items(get_projects_submenu_items(), request, False)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/details/system_card"),
            Navigation.PROJECT_ASSESSMENT_CARD,
        ],
        request,
    )

    # TODO: This now loads an example system card independent of the project ID.
    filepath = Path("example_system_card/system_card.yaml")
    assessment_card_data = get_include_content(filepath.parent, filepath.name, "assessments", assessment_card)

    if not assessment_card_data:
        logger.warning("assessment card not found")
        raise AMTNotFound()

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "assessment_card": assessment_card_data,
        "last_edited": project.last_edited,
        "sub_menu_items": sub_menu_items,
        "breadcrumbs": breadcrumbs,
    }

    return templates.TemplateResponse(request, "pages/assessment_card.html.j2", context)


# !!!
# Implementation of this endpoint is for now independent of the project ID, meaning
# that the same system card is rendered for all project ID's. This is due to the fact
# that the logical process flow of a system card is not complete.
# !!!
@router.get("/{project_id}/details/system_card/models/{model_card}")
async def get_model_card(
    request: Request,
    project_id: int,
    model_card: str,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)

    # TODO: This now loads an example system card independent of the project ID.
    filepath = Path("example_system_card/system_card.yaml")
    model_card_data = get_include_content(filepath.parent, filepath.name, "models", model_card)
    request.state.path_variables.update({"model_card": model_card})

    tab_items = get_project_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/details/system_card"),
            Navigation.PROJECT_MODEL_CARD,
        ],
        request,
    )

    if not model_card_data:
        logger.warning("model card not found")
        raise AMTNotFound()

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "model_card": model_card_data,
        "last_edited": project.last_edited,
        "breadcrumbs": breadcrumbs,
        "project": project,
        "project_id": project.id,
        "tab_items": tab_items,
    }

    return templates.TemplateResponse(request, "pages/model_card.html.j2", context)
