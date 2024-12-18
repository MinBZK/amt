import asyncio
import datetime
import logging
from collections import defaultdict
from collections.abc import Sequence
from typing import Annotated, Any, cast

import yaml
from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from ulid import ULID

from amt.api.deps import templates
from amt.api.forms.measure import get_measure_form
from amt.api.navigation import (
    BaseNavigationItem,
    Navigation,
    NavigationItem,
    resolve_base_navigation_items,
    resolve_navigation_items,
)
from amt.api.routes.shared import get_filters_and_sort_by
from amt.core.authorization import get_user
from amt.core.exceptions import AMTError, AMTNotFound, AMTRepositoryError
from amt.core.internationalization import get_current_translation
from amt.enums.status import Status
from amt.models import Algorithm
from amt.models.task import Task
from amt.repositories.organizations import OrganizationsRepository
from amt.repositories.users import UsersRepository
from amt.schema.measure import ExtendedMeasureTask, MeasureTask, Person
from amt.schema.requirement import RequirementTask
from amt.schema.system_card import Owner, SystemCard
from amt.schema.task import MovedTask
from amt.schema.webform import WebFormOption
from amt.services.algorithms import AlgorithmsService
from amt.services.instruments_and_requirements_state import InstrumentStateService, RequirementsStateService
from amt.services.measures import MeasuresService, create_measures_service
from amt.services.object_storage import ObjectStorageService, create_object_storage_service
from amt.services.organizations import OrganizationsService
from amt.services.requirements import RequirementsService, create_requirements_service
from amt.services.tasks import TasksService

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_instrument_state(system_card: SystemCard) -> dict[str, Any]:
    instrument_state = InstrumentStateService(system_card)
    instrument_states = await instrument_state.get_state_per_instrument()
    return {
        "instrument_states": instrument_states,
        "count_0": instrument_state.get_amount_completed_instruments(),
        "count_1": instrument_state.get_amount_total_instruments(),
    }


async def get_requirements_state(system_card: SystemCard) -> dict[str, Any]:
    requirements_service = create_requirements_service()
    requirements = await requirements_service.fetch_requirements(
        [requirement.urn for requirement in system_card.requirements]
    )
    requirements_state_service = RequirementsStateService(system_card)
    requirements_state = requirements_state_service.get_requirements_state(requirements)

    return {
        "states": requirements_state,
        "count_0": requirements_state_service.get_amount_completed_requirements(),
        "count_1": requirements_state_service.get_amount_total_requirements(),
    }


async def get_algorithm_or_error(
    algorithm_id: int, algorithms_service: AlgorithmsService, request: Request
) -> Algorithm:
    try:
        logger.debug(f"getting algorithm with id {algorithm_id}")
        algorithm = await algorithms_service.get(algorithm_id)
        request.state.path_variables = {"algorithm_id": algorithm_id}
    except AMTRepositoryError as e:
        raise AMTNotFound from e
    return algorithm


def get_user_id_or_error(request: Request) -> str:
    user = get_user(request)
    if user is None or user["sub"] is None:
        raise AMTError
    return user["sub"]


def get_measure_task_or_error(system_card: SystemCard, measure_urn: str) -> MeasureTask:
    measure_task = find_measure_task(system_card, measure_urn)
    if not measure_task:
        raise AMTNotFound
    return measure_task


def get_algorithm_details_tabs(request: Request) -> list[NavigationItem]:
    return resolve_navigation_items(
        [
            Navigation.ALGORITHM_INFO,
            Navigation.ALGORITHM_ALGORITHM_DETAILS,
            Navigation.ALGORITHM_MODEL,
            Navigation.ALGORITHM_REQUIREMENTS,
            Navigation.ALGORITHM_DATA_CARD,
            Navigation.ALGORITHM_TASKS,
            Navigation.ALGORITHM_INSTRUMENTS,
        ],
        request,
    )


def get_algorithms_submenu_items() -> list[BaseNavigationItem]:
    return [
        Navigation.ALGORITHMS_OVERVIEW,
        Navigation.ALGORITHM_TASKS,
        Navigation.ALGORITHM_SYSTEM_CARD,
    ]


async def gather_algorithm_tasks(algorithm_id: int, task_service: TasksService) -> dict[Status, Sequence[Task]]:
    fetch_tasks = [task_service.get_tasks_for_algorithm(algorithm_id, status + 0) for status in Status]

    results = await asyncio.gather(*fetch_tasks)

    return dict(zip(Status, results, strict=True))


@router.get("/{algorithm_id}/details/tasks")
async def get_tasks(
    request: Request,
    algorithm_id: int,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    tasks_service: Annotated[TasksService, Depends(TasksService)],
) -> HTMLResponse:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)
    tab_items = get_algorithm_details_tabs(request)
    tasks_by_status = await gather_algorithm_tasks(algorithm_id, task_service=tasks_service)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details/system_card"),
            Navigation.ALGORITHM_TASKS,
        ],
        request,
    )

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "tasks_by_status": tasks_by_status,
        "statuses": Status,
        "algorithm": algorithm,
        "algorithm_id": algorithm.id,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
    }

    return templates.TemplateResponse(request, "algorithms/tasks.html.j2", context)


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


async def get_algorithm_context(
    algorithm_id: int, algorithms_service: AlgorithmsService, request: Request
) -> tuple[Algorithm, dict[str, Any]]:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)
    tab_items = get_algorithm_details_tabs(request)
    return algorithm, {
        "last_edited": algorithm.last_edited,
        "system_card": algorithm.system_card,
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "algorithm": algorithm,
        "algorithm_id": algorithm.id,
        "tab_items": tab_items,
    }


@router.get("/{algorithm_id}/details")
async def get_algorithm_details(
    request: Request, algorithm_id: int, algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)]
) -> HTMLResponse:
    algorithm, context = await get_algorithm_context(algorithm_id, algorithms_service, request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details/system_card"),
            Navigation.ALGORITHM_DETAILS,
        ],
        request,
    )

    context["breadcrumbs"] = breadcrumbs
    context["base_href"] = f"/algorithm/{ algorithm_id }"

    return templates.TemplateResponse(request, "algorithms/details_info.html.j2", context)


@router.get("/{algorithm_id}/edit/{path:path}")
async def get_algorithm_edit(
    request: Request,
    algorithm_id: int,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    organizations_service: Annotated[OrganizationsService, Depends(OrganizationsService)],
    path: str,
    edit_type: str = "systemcard",
) -> HTMLResponse:
    algorithm, context = await get_algorithm_context(algorithm_id, algorithms_service, request)
    context.update(
        {
            "path": path.replace("/", "."),
            "edit_type": edit_type,
            "object": algorithm,
            "base_href": f"/algorithm/{ algorithm_id }",
        }
    )

    if edit_type == "select_my_organizations":
        user = get_user(request)

        my_organizations = await organizations_service.get_organizations_for_user(user_id=user["sub"] if user else None)

        context["select_options"] = [
            WebFormOption(value=str(organization.id), display_value=organization.name)
            for organization in my_organizations
        ]

    return templates.TemplateResponse(request, "parts/edit_cell.html.j2", context)


@router.get("/{algorithm_id}/cancel/{path:path}")
async def get_algorithm_cancel(
    request: Request,
    algorithm_id: int,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    path: str,
    edit_type: str = "systemcard",
) -> HTMLResponse:
    algorithm, context = await get_algorithm_context(algorithm_id, algorithms_service, request)
    context.update(
        {
            "path": path.replace("/", "."),
            "edit_type": edit_type,
            "base_href": f"/algorithm/{ algorithm_id }",
            "object": algorithm,
        }
    )
    return templates.TemplateResponse(request, "parts/view_cell.html.j2", context)


class UpdateFieldModel(BaseModel):
    value: str


def set_path(algorithm: dict[str, Any] | object, path: str, value: str) -> None:
    if not path:
        raise ValueError("Path cannot be empty")

    attrs = path.lstrip("/").split("/")
    obj: Any = algorithm
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


@router.put("/{algorithm_id}/update/{path:path}")
async def get_algorithm_update(
    request: Request,
    algorithm_id: int,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    organizations_repository: Annotated[OrganizationsRepository, Depends(OrganizationsRepository)],
    update_data: UpdateFieldModel,
    path: str,
    edit_type: str = "systemcard",
) -> HTMLResponse:
    algorithm, context = await get_algorithm_context(algorithm_id, algorithms_service, request)
    context.update(
        {"path": path.replace("/", "."), "edit_type": edit_type, "base_href": f"/algorithm/{ algorithm_id }"}
    )

    if edit_type == "select_my_organizations":
        organization = await organizations_repository.find_by_id(int(update_data.value))
        algorithm.organization = organization
        # TODO: we need to know which organization to update and what to remove
        if not algorithm.system_card.owners:
            algorithm.system_card.owners = [Owner(organization=organization.name, oin=str(organization.id))]
        algorithm.system_card.owners[0].organization = organization.name
    else:
        set_path(algorithm, path, update_data.value)

    algorithm = await algorithms_service.update(algorithm)
    context.update({"object": algorithm})
    return templates.TemplateResponse(request, "parts/view_cell.html.j2", context)


@router.get("/{algorithm_id}/details/system_card")
async def get_system_card(
    request: Request,
    algorithm_id: int,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
) -> HTMLResponse:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)

    tab_items = get_algorithm_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details/system_card"),
            Navigation.ALGORITHM_SYSTEM_CARD,
        ],
        request,
    )

    context = {
        "system_card": algorithm.system_card,
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "last_edited": algorithm.last_edited,
        "algorithm": algorithm,
        "algorithm_id": algorithm.id,
        "tab_items": tab_items,
        "breadcrumbs": breadcrumbs,
    }

    return templates.TemplateResponse(request, "pages/system_card.html.j2", context)


@router.get("/{algorithm_id}/details/model/inference")
async def get_algorithm_inference(
    request: Request, algorithm_id: int, algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)]
) -> HTMLResponse:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(
                custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details/model/inference"
            ),
            Navigation.ALGORITHM_MODEL,
        ],
        request,
    )

    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)

    tab_items = get_algorithm_details_tabs(request)

    context = {
        "last_edited": algorithm.last_edited,
        "system_card": algorithm.system_card,
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "algorithm": algorithm,
        "algorithm_id": algorithm.id,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
    }

    return templates.TemplateResponse(request, "algorithms/details_inference.html.j2", context)


@router.get("/{algorithm_id}/details/system_card/requirements")
async def get_system_card_requirements(
    request: Request,
    algorithm_id: int,
    organizations_repository: Annotated[OrganizationsRepository, Depends(OrganizationsRepository)],
    users_repository: Annotated[UsersRepository, Depends(UsersRepository)],
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    requirements_service: Annotated[RequirementsService, Depends(create_requirements_service)],
    measures_service: Annotated[MeasuresService, Depends(create_measures_service)],
) -> HTMLResponse:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)
    tab_items = get_algorithm_details_tabs(request)
    filters, _, _, sort_by = get_filters_and_sort_by(request)
    organization = await organizations_repository.find_by_id(algorithm.organization_id)
    filters["organization-id"] = str(organization.id)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details/system_card"),
            Navigation.ALGORITHM_SYSTEM_CARD,
        ],
        request,
    )

    requirements = await requirements_service.fetch_requirements(
        [requirement.urn for requirement in algorithm.system_card.requirements]
    )

    # Get measures that correspond to the requirements and merge them with the measure tasks
    requirements_and_measures = []
    measure_tasks: list[MeasureTask | None] = []
    for requirement in requirements:
        completed_measures_count = 0
        linked_measures = await measures_service.fetch_measures(requirement.links)
        extended_linked_measures: list[ExtendedMeasureTask] = []
        for measure in linked_measures:
            measure_task = find_measure_task(algorithm.system_card, measure.urn)
            if measure_task not in measure_tasks:
                measure_tasks.append(measure_task)
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

    measure_task_functions = await get_measure_task_functions(measure_tasks, users_repository, sort_by, filters)

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "algorithm": algorithm,
        "algorithm_id": algorithm.id,
        "tab_items": tab_items,
        "breadcrumbs": breadcrumbs,
        "requirements_and_measures": requirements_and_measures,
        "measure_task_functions": measure_task_functions,
    }

    return templates.TemplateResponse(request, "algorithms/details_requirements.html.j2", context)


async def get_measure_task_functions(
    measure_tasks: list[MeasureTask | None],
    users_repository: Annotated[UsersRepository, Depends(UsersRepository)],
    sort_by: dict[str, str],
    filters: dict[str, str],
) -> dict[str, list[Any]]:
    measure_task_functions: dict[str, list[Any]] = defaultdict(list)
    for measure_task in measure_tasks:
        if measure_task.accountable_persons:  # pyright: ignore [reportOptionalMemberAccess]
            members_accountable = await users_repository.find_all(
                search=measure_task.accountable_persons[0].name,  # pyright: ignore [reportOptionalMemberAccess]
                sort=sort_by,
                filters=filters,
            )
            if members_accountable:
                measure_task_functions[measure_task.urn].append(members_accountable[0])  # pyright: ignore [reportOptionalMemberAccess]

        if measure_task.reviewer_persons:  # pyright: ignore [reportOptionalMemberAccess]
            members_reviewer = await users_repository.find_all(
                search=measure_task.reviewer_persons[0].name,  # pyright: ignore [reportOptionalMemberAccess]
                sort=sort_by,
                filters=filters,
            )
            if members_reviewer:
                measure_task_functions[measure_task.urn].append(members_reviewer[0])  # pyright: ignore [reportOptionalMemberAccess]

        if measure_task.responsible_persons:  # pyright: ignore [reportOptionalMemberAccess]
            members_responsible = await users_repository.find_all(
                search=measure_task.responsible_persons[0].name,  # pyright: ignore [reportOptionalMemberAccess]
                sort=sort_by,
                filters=filters,
            )
            if members_responsible:
                measure_task_functions[measure_task.urn].append(members_responsible[0])  # pyright: ignore [reportOptionalMemberAccess]
    return measure_task_functions


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


async def find_requirement_tasks_by_measure_urn(system_card: SystemCard, measure_urn: str) -> list[RequirementTask]:
    requirement_mapper: dict[str, RequirementTask] = {}
    for requirement_task in system_card.requirements:
        requirement_mapper[requirement_task.urn] = requirement_task

    requirement_tasks: list[RequirementTask] = []
    measures_service = create_measures_service()
    requirements_service = create_requirements_service()
    measure = await measures_service.fetch_measures(measure_urn)
    for requirement_urn in measure[0].links:
        # TODO: This is because measure are linked to too many requirement not applicable in our use case
        if requirement_urn not in requirement_mapper:
            continue

        if len(await requirements_service.fetch_requirements(requirement_urn)) > 0:
            requirement_tasks.append(requirement_mapper[requirement_urn])

    return requirement_tasks


@router.delete("/{algorithm_id}")
async def delete_algorithm(
    request: Request,
    algorithm_id: int,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
) -> HTMLResponse:
    await algorithms_service.delete(algorithm_id)
    return templates.Redirect(request, "/algorithms/")


@router.get("/{algorithm_id}/measure/{measure_urn}")
async def get_measure(
    request: Request,
    organizations_repository: Annotated[OrganizationsRepository, Depends(OrganizationsRepository)],
    users_repository: Annotated[UsersRepository, Depends(UsersRepository)],
    algorithm_id: int,
    measure_urn: str,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    measures_service: Annotated[MeasuresService, Depends(create_measures_service)],
    object_storage_service: Annotated[ObjectStorageService, Depends(create_object_storage_service)],
    search: str = Query(""),
) -> HTMLResponse:
    filters, _, _, sort_by = get_filters_and_sort_by(request)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    measure = await measures_service.fetch_measures([measure_urn])
    measure_task = get_measure_task_or_error(algorithm.system_card, measure_urn)

    filenames: list[tuple[str, str]] = []
    for file in measure_task.files:
        metadata = object_storage_service.get_file_metadata_from_object_name(file)
        filenames.append((file.split("/")[-1], f"{metadata.filename}.{metadata.ext}"))

    organization = await organizations_repository.find_by_id(algorithm.organization_id)
    filters["organization-id"] = str(organization.id)
    members = await users_repository.find_all(search=search, sort=sort_by, filters=filters)

    measure_accountable = measure_task.accountable_persons[0].name if measure_task.accountable_persons else ""  # pyright: ignore [reportOptionalMemberAccess]
    measure_reviewer = measure_task.reviewer_persons[0].name if measure_task.reviewer_persons else ""  # pyright: ignore [reportOptionalMemberAccess]
    measure_responsible = measure_task.responsible_persons[0].name if measure_task.responsible_persons else ""  # pyright: ignore [reportOptionalMemberAccess]

    measure_form = await get_measure_form(
        id="measure_state",
        current_values={
            "measure_state": measure_task.state,
            "measure_value": measure_task.value,
            "measure_links": measure_task.links,
            "measure_files": filenames,
            "measure_accountable": measure_accountable,
            "measure_reviewer": measure_reviewer,
            "measure_responsible": measure_responsible,
        },
        members=members,
        translations=get_current_translation(request),
    )

    context = {"measure": measure[0], "algorithm_id": algorithm_id, "form": measure_form}

    return templates.TemplateResponse(request, "algorithms/details_measure_modal.html.j2", context)


async def get_users_from_function_name(
    measure_accountable: Annotated[str | None, Form()],
    measure_reviewer: Annotated[str | None, Form()],
    measure_responsible: Annotated[str | None, Form()],
    users_repository: Annotated[UsersRepository, Depends(UsersRepository)],
    sort_by: dict[str, str],
    filters: dict[str, str],
) -> tuple[list[Person], list[Person], list[Person]]:
    accountable_persons, reviewer_persons, responsible_persons = [], [], []
    if measure_accountable:
        accountable_member = await users_repository.find_all(search=measure_accountable, sort=sort_by, filters=filters)
        accountable_persons = [Person(name=accountable_member[0].name, uuid=str(accountable_member[0].id))]  # pyright: ignore [reportOptionalMemberAccess]
    if measure_reviewer:
        reviewer_member = await users_repository.find_all(search=measure_reviewer, sort=sort_by, filters=filters)
        reviewer_persons = [Person(name=reviewer_member[0].name, uuid=str(reviewer_member[0].id))]  # pyright: ignore [reportOptionalMemberAccess]
    if measure_responsible:
        responsible_member = await users_repository.find_all(search=measure_responsible, sort=sort_by, filters=filters)
        responsible_persons = [Person(name=responsible_member[0].name, uuid=str(responsible_member[0].id))]  # pyright: ignore [reportOptionalMemberAccess]
    return accountable_persons, reviewer_persons, responsible_persons


@router.post("/{algorithm_id}/measure/{measure_urn}")
async def update_measure_value(
    request: Request,
    algorithm_id: int,
    measure_urn: str,
    organizations_repository: Annotated[OrganizationsRepository, Depends(OrganizationsRepository)],
    users_repository: Annotated[UsersRepository, Depends(UsersRepository)],
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    requirements_service: Annotated[RequirementsService, Depends(create_requirements_service)],
    object_storage_service: Annotated[ObjectStorageService, Depends(create_object_storage_service)],
    measure_state: Annotated[str, Form()],
    measure_responsible: Annotated[str | None, Form()] = None,
    measure_reviewer: Annotated[str | None, Form()] = None,
    measure_accountable: Annotated[str | None, Form()] = None,
    measure_value: Annotated[str | None, Form()] = None,
    measure_links: Annotated[list[str] | None, Form()] = None,
    measure_files: Annotated[list[UploadFile] | None, File()] = None,
) -> HTMLResponse:
    filters, _, _, sort_by = get_filters_and_sort_by(request)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    user_id = get_user_id_or_error(request)
    measure_task = get_measure_task_or_error(algorithm.system_card, measure_urn)

    paths = (
        object_storage_service.upload_files(
            algorithm.organization_id, algorithm.id, measure_urn, user_id, measure_files
        )
        if measure_files
        else None
    )
    accountable_persons, reviewer_persons, responsible_persons = await get_users_from_function_name(
        measure_accountable, measure_reviewer, measure_responsible, users_repository, sort_by, filters
    )

    measure_task.update(
        measure_state, measure_value, measure_links, paths, responsible_persons, accountable_persons, reviewer_persons
    )
    organization = await organizations_repository.find_by_id(algorithm.organization_id)
    filters["organization-id"] = str(organization.id)

    # update for the linked requirements the state based on all it's measures
    requirement_tasks = await find_requirement_tasks_by_measure_urn(algorithm.system_card, measure_urn)
    requirement_urns = [requirement_task.urn for requirement_task in requirement_tasks]
    requirements = await requirements_service.fetch_requirements(requirement_urns)

    for requirement in requirements:
        count_completed = 0
        for link_measure_urn in requirement.links:
            link_measure_task = find_measure_task(algorithm.system_card, link_measure_urn)
            if link_measure_task:  # noqa: SIM102
                if link_measure_task.state == "done":
                    count_completed += 1
        requirement_task = find_requirement_task(algorithm.system_card, requirement.urn)
        if count_completed == len(requirement.links):
            requirement_task.state = "done"  # pyright: ignore [reportOptionalMemberAccess]
        elif count_completed == 0 and len(requirement.links) > 0:
            requirement_task.state = "to do"  # pyright: ignore [reportOptionalMemberAccess]
        else:
            requirement_task.state = "in progress"  # pyright: ignore [reportOptionalMemberAccess]

    await algorithms_service.update(algorithm)
    # TODO: FIX THIS!! The page now reloads at the top, which is annoying
    return templates.Redirect(request, f"/algorithm/{algorithm_id}/details/system_card/requirements")


@router.get("/{algorithm_id}/details/system_card/data")
async def get_system_card_data_page(
    request: Request,
    algorithm_id: int,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
) -> HTMLResponse:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)

    tab_items = get_algorithm_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details/system_card"),
            Navigation.ALGORITHM_SYSTEM_CARD,
        ],
        request,
    )

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "algorithm": algorithm,
        "algorithm_id": algorithm.id,
        "tab_items": tab_items,
        "breadcrumbs": breadcrumbs,
    }

    return templates.TemplateResponse(request, "algorithms/details_data.html.j2", context)


@router.get("/{algorithm_id}/details/system_card/instruments")
async def get_system_card_instruments(
    request: Request,
    algorithm_id: int,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
) -> HTMLResponse:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)

    tab_items = get_algorithm_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details/system_card"),
            Navigation.ALGORITHM_SYSTEM_CARD,
        ],
        request,
    )

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "algorithm": algorithm,
        "algorithm_id": algorithm.id,
        "tab_items": tab_items,
        "breadcrumbs": breadcrumbs,
    }

    return templates.TemplateResponse(request, "algorithms/details_instruments.html.j2", context)


@router.get("/{algorithm_id}/details/system_card/assessments/{assessment_card}")
async def get_assessment_card(
    request: Request,
    algorithm_id: int,
    assessment_card: str,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
) -> HTMLResponse:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)

    request.state.path_variables.update({"assessment_card": assessment_card})

    sub_menu_items = resolve_navigation_items(get_algorithms_submenu_items(), request, False)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details/system_card"),
            Navigation.ALGORITHM_ASSESSMENT_CARD,
        ],
        request,
    )

    assessment_card_data = next(
        (
            assessment
            for assessment in algorithm.system_card.assessments
            if assessment.name is not None and assessment.name.lower() == assessment_card
        ),
        None,
    )

    if not assessment_card_data:
        logger.warning("assessment card not found")
        raise AMTNotFound()

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "assessment_card": assessment_card_data,
        "last_edited": algorithm.last_edited,
        "sub_menu_items": sub_menu_items,
        "breadcrumbs": breadcrumbs,
    }

    return templates.TemplateResponse(request, "pages/assessment_card.html.j2", context)


@router.get("/{algorithm_id}/details/system_card/models/{model_card}")
async def get_model_card(
    request: Request,
    algorithm_id: int,
    model_card: str,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
) -> HTMLResponse:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    request.state.path_variables.update({"model_card": model_card})
    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)

    tab_items = get_algorithm_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details/system_card"),
            Navigation.ALGORITHM_MODEL_CARD,
        ],
        request,
    )

    model_card_data = next(
        (
            model
            for model in algorithm.system_card.models
            if (model.name is not None and model.name.lower() == model_card)
        ),
        None,
    )

    if not model_card_data:
        logger.warning("model card not found")
        raise AMTNotFound()

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "model_card": model_card_data,
        "last_edited": algorithm.last_edited,
        "breadcrumbs": breadcrumbs,
        "algorithm": algorithm,
        "algorithm_id": algorithm.id,
        "tab_items": tab_items,
    }

    return templates.TemplateResponse(request, "pages/model_card.html.j2", context)


@router.get("/{algorithm_id}/details/system_card/download")
async def download_algorithm_system_card_as_yaml(
    algorithm_id: int, algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)], request: Request
) -> FileResponse:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    filename = algorithm.name + "_" + datetime.datetime.now(datetime.UTC).isoformat() + ".yaml"
    with open(filename, "w") as outfile:
        yaml.dump(algorithm.system_card.model_dump(), outfile)
    try:
        return FileResponse(filename, filename=filename)
    except AMTRepositoryError as e:
        raise AMTNotFound from e


@router.get("/{algorithm_id}/file/{ulid}")
async def get_file(
    request: Request,
    algorithm_id: int,
    ulid: ULID,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    object_storage_service: Annotated[ObjectStorageService, Depends(create_object_storage_service)],
) -> Response:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    file = object_storage_service.get_file(algorithm.organization_id, algorithm_id, ulid)
    file_metadata = object_storage_service.get_file_metadata(algorithm.organization_id, algorithm_id, ulid)

    return Response(
        content=file.read(decode_content=True),
        headers={
            "Content-Disposition": f"attachment;filename={file_metadata.filename}.{file_metadata.ext}",
            "Content-Type": "application/octet-stream",
        },
    )


@router.delete("/{algorithm_id}/file/{ulid}")
async def delete_file(
    request: Request,
    algorithm_id: int,
    ulid: ULID,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    object_storage_service: Annotated[ObjectStorageService, Depends(create_object_storage_service)],
) -> HTMLResponse:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    metadata = object_storage_service.get_file_metadata(algorithm.organization_id, algorithm_id, ulid)
    measure_task = get_measure_task_or_error(algorithm.system_card, metadata.measure_urn)

    entry_to_delete = object_storage_service.delete_file(algorithm.organization_id, algorithm_id, ulid)
    measure_task.files.remove(entry_to_delete)
    await algorithms_service.update(algorithm)

    return HTMLResponse(content="", status_code=200)
