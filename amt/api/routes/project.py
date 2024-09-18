import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from amt.api.deps import templates
from amt.api.navigation import (
    BaseNavigationItem,
    Navigation,
    resolve_base_navigation_items,
    resolve_sub_menu,
)
from amt.core.exceptions import NotFound, RepositoryError
from amt.enums.status import Status
from amt.models import Project
from amt.services.projects import ProjectsService
from amt.services.storage import StorageFactory
from amt.services.tasks import TasksService
from amt.utils.storage import get_include_content, last_modified_at

router = APIRouter()
logger = logging.getLogger(__name__)


def get_project_or_error(project_id: int, projects_service: ProjectsService, request: Request) -> Project:
    try:
        logger.debug(f"getting project with id {project_id}")
        project = projects_service.get(project_id)
        request.state.path_variables = {"project_id": project_id}
    except RepositoryError as e:
        raise NotFound from e
    return project


def get_projects_submenu_items() -> list[BaseNavigationItem]:
    return [
        Navigation.PROJECTS_OVERVIEW,
        Navigation.PROJECT_TASKS,
        Navigation.PROJECT_SYSTEM_CARD,
    ]


@router.get("/{project_id}/tasks")
async def get_tasks(
    request: Request,
    project_id: int,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
    tasks_service: Annotated[TasksService, Depends(TasksService)],
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)

    sub_menu_items = resolve_sub_menu(get_projects_submenu_items(), request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/system_card"),
            Navigation.PROJECT_TASKS,
        ],
        request,
    )

    context = {
        "tasks_service": tasks_service,
        "statuses": Status,
        "project": project,
        "breadcrumbs": breadcrumbs,
        "sub_menu_items": sub_menu_items,
    }

    return templates.TemplateResponse(request, "projects/tasks.html.j2", context)


@router.get("/{project_id}")
async def get_project_details(
    request: Request, project_id: int, projects_service: Annotated[ProjectsService, Depends(ProjectsService)]
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)

    sub_menu_items = resolve_sub_menu(get_projects_submenu_items(), request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/system_card"),
            Navigation.PROJECT_DETAILS,
        ],
        request,
    )

    context = {"project": project, "breadcrumbs": breadcrumbs, "sub_menu_items": sub_menu_items}

    return templates.TemplateResponse(request, "projects/details.html.j2", context)


# !!!
# Implementation of this endpoint is for now independent of the project ID, meaning
# that the same system card is rendered for all project ID's. This is due to the fact
# that the logical process flow of a system card is not complete.
# !!!
@router.get("/{project_id}/system_card")
async def get_system_card(
    request: Request,
    project_id: int,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)

    sub_menu_items = resolve_sub_menu(get_projects_submenu_items(), request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/system_card"),
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
        "last_updated": last_modified_at(filepath),
        "project_id": project.id,
        "sub_menu_items": sub_menu_items,
        "breadcrumbs": breadcrumbs,
    }

    return templates.TemplateResponse(request, "pages/system_card.html.j2", context)


# !!!
# Implementation of this endpoint is for now independent of the project ID, meaning
# that the same system card is rendered for all project ID's. This is due to the fact
# that the logical process flow of a system card is not complete.
# !!!
@router.get("/{project_id}/system_card/assessments/{assessment_card}")
async def get_assessment_card(
    request: Request,
    project_id: int,
    assessment_card: str,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)

    request.state.path_variables.update({"assessment_card": assessment_card})

    sub_menu_items = resolve_sub_menu(get_projects_submenu_items(), request, False)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/system_card"),
            Navigation.PROJECT_ASSESSMENT_CARD,
        ],
        request,
    )

    # TODO: This now loads an example system card independent of the project ID.
    filepath = Path("example_system_card/system_card.yaml")
    assessment_card_data = get_include_content(filepath.parent, filepath.name, "assessments", assessment_card)

    if not assessment_card_data:
        logger.warning("assessment card not found")
        raise NotFound()

    context = {
        "assessment_card": assessment_card_data,
        "last_updated": last_modified_at(filepath),
        "sub_menu_items": sub_menu_items,
        "breadcrumbs": breadcrumbs,
    }

    return templates.TemplateResponse(request, "pages/assessment_card.html.j2", context)


# !!!
# Implementation of this endpoint is for now independent of the project ID, meaning
# that the same system card is rendered for all project ID's. This is due to the fact
# that the logical process flow of a system card is not complete.
# !!!
@router.get("/{project_id}/system_card/models/{model_card}")
async def get_model_card(
    request: Request,
    project_id: int,
    model_card: str,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
) -> HTMLResponse:
    project = get_project_or_error(project_id, projects_service, request)

    # TODO: This now loads an example system card independent of the project ID.
    filepath = Path("example_system_card/system_card.yaml")
    model_card_data = get_include_content(filepath.parent, filepath.name, "models", model_card)

    request.state.path_variables.update({"model_card": model_card})

    sub_menu_items = resolve_sub_menu(get_projects_submenu_items(), request, False)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(custom_display_text=project.name, url="/project/{project_id}/system_card"),
            Navigation.PROJECT_MODEL_CARD,
        ],
        request,
    )

    if not model_card_data:
        logger.warning("model card not found")
        raise NotFound()

    context = {
        "model_card": model_card_data,
        "last_updated": last_modified_at(filepath),
        "sub_menu_items": sub_menu_items,
        "breadcrumbs": breadcrumbs,
    }

    return templates.TemplateResponse(request, "pages/model_card.html.j2", context)
