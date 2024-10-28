import asyncio
import functools
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from amt.api.deps import templates
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
from amt.models.task import Task
from amt.schema.measure import ExtendedMeasureTask, MeasureTask
from amt.schema.requirement import RequirementTask
from amt.schema.system_card import SystemCard
from amt.schema.task import MovedTask
from amt.services import task_registry
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


async def get_project_or_error(project_id: int, projects_service: ProjectsService, request: Request) -> Project:
    try:
        logger.debug(f"getting project with id {project_id}")
        project = await projects_service.get(project_id)
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


async def gather_project_tasks(project_id: int, task_service: TasksService) -> dict[Status, Sequence[Task]]:
    fetch_tasks = [task_service.get_tasks_for_project(project_id, status + 0) for status in Status]

    results = await asyncio.gather(*fetch_tasks)

    return dict(zip(Status, results, strict=True))


@router.get("/{project_id}/details/tasks")
async def get_tasks(
    request: Request,
    project_id: int,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
    tasks_service: Annotated[TasksService, Depends(TasksService)],
) -> HTMLResponse:
    project = await get_project_or_error(project_id, projects_service, request)
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)
    tab_items = get_project_details_tabs(request)
    tasks_by_status = await gather_project_tasks(project_id, task_service=tasks_service)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(
                custom_display_text=project.name, url="/algorithm-system/{project_id}/details/system_card"
            ),
            Navigation.PROJECT_TASKS,
        ],
        request,
    )

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "tasks_by_status": tasks_by_status,
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
    task = await tasks_service.move_task(
        moved_task.id,
        moved_task.status_id,
        moved_task.previous_sibling_id,
        moved_task.next_sibling_id,
    )

    context = {"task": task}

    return templates.TemplateResponse(request, "parts/task.html.j2", context=context)


async def get_project_context(
    project_id: int, projects_service: ProjectsService, request: Request
) -> tuple[Project, dict[str, Any]]:
    project = await get_project_or_error(project_id, projects_service, request)
    system_card_data = get_system_card_data()
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)
    tab_items = get_project_details_tabs(request)
    project.system_card = system_card_data
    return project, {
        "last_edited": project.last_edited,
        "system_card": system_card_data,
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "project": project,
        "project_id": project.id,
        "tab_items": tab_items,
    }


@router.get("/{project_id}/details")
async def get_project_details(
    request: Request, project_id: int, projects_service: Annotated[ProjectsService, Depends(ProjectsService)]
) -> HTMLResponse:
    project, context = await get_project_context(project_id, projects_service, request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(
                custom_display_text=project.name, url="/algorithm-system/{project_id}/details/system_card"
            ),
            Navigation.PROJECT_DETAILS,
        ],
        request,
    )

    context["breadcrumbs"] = breadcrumbs

    return templates.TemplateResponse(request, "projects/details_info.html.j2", context)


@router.get("/{project_id}/edit/{path:path}")
async def get_project_edit(
    request: Request,
    project_id: int,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
    path: str,
) -> HTMLResponse:
    _, context = await get_project_context(project_id, projects_service, request)
    context["path"] = path.replace("/", ".")
    return templates.TemplateResponse(request, "parts/edit_cell.html.j2", context)


@router.get("/{project_id}/cancel/{path:path}")
async def get_project_cancel(
    request: Request,
    project_id: int,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
    path: str,
) -> HTMLResponse:
    _, context = await get_project_context(project_id, projects_service, request)
    context["path"] = path.replace("/", ".")
    return templates.TemplateResponse(request, "parts/view_cell.html.j2", context)


class UpdateFieldModel(BaseModel):
    value: str


def set_path(project: dict[str, Any] | object, path: str, value: str) -> None:
    if not path:
        raise ValueError("Path cannot be empty")

    attrs = path.lstrip("/").split("/")
    obj: Any = project
    for attr in attrs[:-1]:
        if isinstance(obj, dict):
            obj = cast(dict[str, Any], obj)
            if attr not in obj:
                obj[attr] = {}
            obj = obj[attr]
        else:
            if not hasattr(obj, attr):
                setattr(obj, attr, {})
            obj = getattr(obj, attr)

    if isinstance(obj, dict):
        obj[attrs[-1]] = value
    else:
        setattr(obj, attrs[-1], value)


@router.put("/{project_id}/update/{path:path}")
async def get_project_update(
    request: Request,
    project_id: int,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
    update_data: UpdateFieldModel,
    path: str,
) -> HTMLResponse:
    project, context = await get_project_context(project_id, projects_service, request)
    set_path(project, path, update_data.value)
    await projects_service.update(project)
    context["path"] = path.replace("/", ".")
    return templates.TemplateResponse(request, "parts/view_cell.html.j2", context)


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
    project = await get_project_or_error(project_id, projects_service, request)
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)

    tab_items = get_project_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(
                custom_display_text=project.name, url="/algorithm-system/{project_id}/details/system_card"
            ),
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
    project = await get_project_or_error(project_id, projects_service, request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(
                custom_display_text=project.name, url="/algorithm-system/{project_id}/details/model/inference"
            ),
            Navigation.PROJECT_MODEL,
        ],
        request,
    )

    system_card_data = get_system_card_data()
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)

    tab_items = get_project_details_tabs(request)

    context = {
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
    project = await get_project_or_error(project_id, projects_service, request)
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)
    # TODO: This tab is fairly slow, fix in later releases
    tab_items = get_project_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(
                custom_display_text=project.name, url="/algorithm-system/{project_id}/details/system_card"
            ),
            Navigation.PROJECT_SYSTEM_CARD,
        ],
        request,
    )

    # TODO: This is only for the demo of 18 Oct. In reality one would load the requirements from the requirement
    # field in the system card, but one would load the AI Act Profile and determine the requirements from
    # the labels in this field.
    system_card = project.system_card
    requirements = fetch_requirements([requirement.urn for requirement in system_card.requirements])

    # Get measures that correspond to the requirements and merge them with the measuretasks
    requirements_and_measures = []
    for requirement in requirements:
        completed_measures_count = 0
        linked_measures = fetch_measures(requirement.links)
        extended_linked_measures: list[ExtendedMeasureTask] = []
        for measure in linked_measures:
            measure_task = find_measure_task(system_card, measure.urn)
            if measure_task:
                ext_measure_task = ExtendedMeasureTask(
                    name=measure.name,
                    description=measure.description,
                    urn=measure.urn,
                    state=measure_task.state,
                    value=measure_task.value,
                    version=measure_task.version,
                )
                if ext_measure_task.state == "done":
                    completed_measures_count += 1
                extended_linked_measures.append(ext_measure_task)
        requirements_and_measures.append((requirement, completed_measures_count, extended_linked_measures))  # pyright: ignore [reportUnknownMemberType]

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


def find_measure_task(system_card: SystemCard, urn: str) -> MeasureTask | None:
    for measure in system_card.measures:
        if measure.urn == urn:
            return measure
    return None


def find_requirement_task(system_card: SystemCard, requirement_urn: str) -> RequirementTask | None:
    for requirement in system_card.requirements:
        if requirement.urn == requirement_urn:
            return requirement
    return None


def find_requirement_tasks_by_measure_urn(system_card: SystemCard, measure_urn: str) -> list[RequirementTask]:
    requirement_mapper: dict[str, RequirementTask] = {}
    for requirement_task in system_card.requirements:
        requirement_mapper[requirement_task.urn] = requirement_task

    requirement_tasks: list[RequirementTask] = []
    measure = fetch_measures([measure_urn])
    for requirement_urn in measure[0].links:
        # TODO: This is because measure are linked to too many requirement not applicable in our use case
        if len(fetch_requirements([requirement_urn])) > 0:
            requirement_tasks.append(requirement_mapper[requirement_urn])

    return requirement_tasks


@router.get("/{project_id}/measure/{measure_urn}")
async def get_measure(
    request: Request,
    project_id: int,
    measure_urn: str,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
) -> HTMLResponse:
    project = await get_project_or_error(project_id, projects_service, request)
    measure = task_registry.fetch_measures([measure_urn])
    measure_task = find_measure_task(project.system_card, measure_urn)

    context = {
        "measure": measure[0],
        "measure_state": measure_task.state,  # pyright: ignore [reportOptionalMemberAccess]
        "measure_value": measure_task.value,  # pyright: ignore [reportOptionalMemberAccess]
        "project_id": project_id,
    }

    return templates.TemplateResponse(request, "projects/details_measure_modal.html.j2", context)


class MeasureUpdate(BaseModel):
    measure_state: str = Field(default=None)
    measure_value: str = Field(default=None)


@router.post("/{project_id}/measure/{measure_urn}")
async def update_measure_value(
    request: Request,
    project_id: int,
    measure_urn: str,
    measure_update: MeasureUpdate,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
) -> HTMLResponse:
    project = await get_project_or_error(project_id, projects_service, request)

    measure_task = find_measure_task(project.system_card, measure_urn)
    measure_task.state = measure_update.measure_state  # pyright: ignore [reportOptionalMemberAccess]
    measure_task.value = measure_update.measure_value  # pyright: ignore [reportOptionalMemberAccess]

    # update for the linked requirements the state based on all it's measures
    requirement_tasks = find_requirement_tasks_by_measure_urn(project.system_card, measure_urn)
    requirement_urns = [requirement_task.urn for requirement_task in requirement_tasks]
    requirements = fetch_requirements(requirement_urns)

    for requirement in requirements:
        count_completed = 0
        for link_measure_urn in requirement.links:
            link_measure_task = find_measure_task(project.system_card, link_measure_urn)
            if link_measure_task:  # noqa: SIM102
                if link_measure_task.state == "done":
                    count_completed += 1
        requirement_task = find_requirement_task(project.system_card, requirement.urn)
        if count_completed == len(requirement.links):
            requirement_task.state = "done"  # pyright: ignore [reportOptionalMemberAccess]
        elif count_completed == 0 and len(requirement.links) > 0:
            requirement_task.state = "to do"  # pyright: ignore [reportOptionalMemberAccess]
        else:
            requirement_task.state = "in progress"  # pyright: ignore [reportOptionalMemberAccess]

    await projects_service.update(project)
    # TODO: FIX THIS!! The page now reloads at the top, which is annoying
    return templates.Redirect(request, f"/algorithm-system/{project_id}/details/system_card/requirements")


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
    project = await get_project_or_error(project_id, projects_service, request)
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)

    tab_items = get_project_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(
                custom_display_text=project.name, url="/algorithm-system/{project_id}/details/system_card"
            ),
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
    project = await get_project_or_error(project_id, projects_service, request)
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)

    tab_items = get_project_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(
                custom_display_text=project.name, url="/algorithm-system/{project_id}/details/system_card"
            ),
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
    project = await get_project_or_error(project_id, projects_service, request)
    instrument_state = get_instrument_state()
    requirements_state = get_requirements_state(project.system_card)

    request.state.path_variables.update({"assessment_card": assessment_card})

    sub_menu_items = resolve_navigation_items(get_projects_submenu_items(), request, False)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.PROJECTS_ROOT,
            BaseNavigationItem(
                custom_display_text=project.name, url="/algorithm-system/{project_id}/details/system_card"
            ),
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
    project = await get_project_or_error(project_id, projects_service, request)
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
            BaseNavigationItem(
                custom_display_text=project.name, url="/algorithm-system/{project_id}/details/system_card"
            ),
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
