import asyncio
import datetime
import logging
from collections import defaultdict
from collections.abc import Sequence
from typing import Annotated, Any

import yaml
from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from ulid import ULID

from amt.api.decorators import permission
from amt.api.deps import templates
from amt.api.editable import (
    EditModes,
    ResolvedEditable,
    get_enriched_resolved_editable,
    get_resolved_editables,
    save_editable,
)
from amt.api.forms.measure import get_measure_form
from amt.api.navigation import (
    BaseNavigationItem,
    Navigation,
    NavigationItem,
    resolve_base_navigation_items,
    resolve_navigation_items,
)
from amt.api.routes.shared import UpdateFieldModel, get_filters_and_sort_by, replace_none_with_empty_string_inplace
from amt.core.authorization import AuthorizationResource, AuthorizationVerb, get_user
from amt.core.exceptions import AMTError, AMTNotFound, AMTRepositoryError
from amt.core.internationalization import get_current_translation
from amt.enums.status import Status
from amt.models import Algorithm, User
from amt.models.task import Task
from amt.repositories.organizations import OrganizationsRepository
from amt.repositories.users import UsersRepository
from amt.schema.measure import ExtendedMeasureTask, MeasureTask, Person
from amt.schema.requirement import RequirementTask
from amt.schema.system_card import SystemCard
from amt.schema.task import MovedTask
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
            Navigation.ALGORITHM_COMPLIANCE,
            Navigation.ALGORITHM_TASKS,
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
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
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


@router.get("/{algorithm_id}/edit")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.UPDATE]})
async def get_algorithm_edit(
    request: Request,
    algorithm_id: int,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    organizations_service: Annotated[OrganizationsService, Depends(OrganizationsService)],
    full_resource_path: str,
) -> HTMLResponse:
    user_id = get_user_id_or_error(request)

    editable: ResolvedEditable = await get_enriched_resolved_editable(
        context_variables={"algorithm_id": algorithm_id},
        full_resource_path=full_resource_path,
        algorithms_service=algorithms_service,
        organizations_service=organizations_service,
        edit_mode=EditModes.EDIT,
        user_id=user_id,
        request=request,
    )

    editable_context = {
        "organizations_service": organizations_service,
    }

    if editable.converter:
        editable.value = await editable.converter.read(editable.value, **editable_context)

    context = {
        "base_href": f"/algorithm/{ algorithm_id }",
        "editable_object": editable,
    }

    return templates.TemplateResponse(request, "parts/edit_cell.html.j2", context)


@router.get("/{algorithm_id}/cancel")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.UPDATE]})
async def get_algorithm_cancel(
    request: Request,
    algorithm_id: int,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    organizations_service: Annotated[OrganizationsService, Depends(OrganizationsService)],
    full_resource_path: str,
) -> HTMLResponse:
    editable: ResolvedEditable = await get_enriched_resolved_editable(
        context_variables={"algorithm_id": algorithm_id},
        full_resource_path=full_resource_path,
        algorithms_service=algorithms_service,
        organizations_service=organizations_service,
        edit_mode=EditModes.VIEW,
    )

    editable_context = {"organizations_service": organizations_service, "algorithms_service": algorithms_service}

    if editable.converter:
        editable.value = await editable.converter.view(editable.value, **editable_context)

    context = {
        "relative_resource_path": editable.relative_resource_path.replace("/", ".")
        if editable.relative_resource_path
        else "",
        "base_href": f"/algorithm/{ algorithm_id }",
        "resource_object": editable.resource_object,
        "full_resource_path": full_resource_path,
        "editable_object": editable,
    }

    return templates.TemplateResponse(request, "parts/view_cell.html.j2", context)


@router.put("/{algorithm_id}/update")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.UPDATE]})
async def get_algorithm_update(
    request: Request,
    algorithm_id: int,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    organizations_service: Annotated[OrganizationsService, Depends(OrganizationsService)],
    update_data: UpdateFieldModel,
    full_resource_path: str,
) -> HTMLResponse:
    user_id = get_user_id_or_error(request)

    editable: ResolvedEditable = await get_enriched_resolved_editable(
        context_variables={"algorithm_id": algorithm_id},
        full_resource_path=full_resource_path,
        algorithms_service=algorithms_service,
        organizations_service=organizations_service,
        edit_mode=EditModes.SAVE,
    )

    editable_context = {
        "user_id": user_id,
        "new_value": update_data.value,
        "organizations_service": organizations_service,
    }

    editable = await save_editable(
        editable,
        update_data=update_data,
        editable_context=editable_context,
        algorithms_service=algorithms_service,
        organizations_service=organizations_service,
        do_save=True,
    )

    # set the value back to view mode if needed
    if editable.converter:
        editable.value = await editable.converter.view(editable.value, **editable_context)

    context = {
        "relative_resource_path": editable.relative_resource_path.replace("/", ".")
        if editable.relative_resource_path
        else "",
        "base_href": f"/algorithm/{ algorithm_id }",
        "resource_object": editable.resource_object,
        "full_resource_path": full_resource_path,
        "editable_object": editable,
    }

    return templates.TemplateResponse(request, "parts/view_cell.html.j2", context)


@router.get("/{algorithm_id}/details/system_card")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
async def get_system_card(
    request: Request,
    algorithm_id: int,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
) -> HTMLResponse:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)

    editables = get_resolved_editables(context_variables={"algorithm_id": algorithm_id})

    tab_items = get_algorithm_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details/system_card"),
            Navigation.ALGORITHM_SYSTEM_CARD,
        ],
        request,
    )

    system_card = algorithm.system_card
    replace_none_with_empty_string_inplace(system_card)

    context = {
        "system_card": system_card,
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "last_edited": algorithm.last_edited,
        "algorithm": algorithm,
        "algorithm_id": algorithm.id,
        "tab_items": tab_items,
        "breadcrumbs": breadcrumbs,
        "editables": editables,
        "base_href": f"/algorithm/{ algorithm_id }",
    }

    return templates.TemplateResponse(request, "pages/system_card.html.j2", context)


@router.get("/{algorithm_id}/details/system_card/compliance")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
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
            Navigation.ALGORITHM_COMPLIANCE,
        ],
        request,
    )

    requirements = await requirements_service.fetch_requirements(
        [requirement.urn for requirement in algorithm.system_card.requirements]
    )

    # Get measures that correspond to the requirements and merge them with the measure tasks
    requirements_and_measures = []
    measure_tasks: list[MeasureTask] = []
    for requirement in requirements:
        completed_measures_count = 0
        linked_measures = await measures_service.fetch_measures(requirement.links)
        extended_linked_measures: list[ExtendedMeasureTask] = []
        for measure in linked_measures:
            measure_task = find_measure_task(algorithm.system_card, measure.urn)
            if measure_task is not None and measure_task not in measure_tasks:
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

    measure_task_functions: dict[str, list[User]] = await get_measure_task_functions(
        measure_tasks, users_repository, sort_by, filters
    )

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

    return templates.TemplateResponse(request, "algorithms/details_compliance.html.j2", context)


async def _fetch_members(
    users_repository: UsersRepository,
    search_name: str,
    sort_by: dict[str, str],
    filters: dict[str, str | list[str | int]],
) -> User | None:
    members = await users_repository.find_all(search=search_name, sort=sort_by, filters=filters)
    return members[0] if members else None


async def get_measure_task_functions(
    measure_tasks: list[MeasureTask],
    users_repository: Annotated[UsersRepository, Depends(UsersRepository)],
    sort_by: dict[str, str],
    filters: dict[str, str | list[str | int]],
) -> dict[str, list[User]]:
    measure_task_functions: dict[str, list[User]] = defaultdict(list)

    for measure_task in measure_tasks:
        person_types = ["accountable_persons", "reviewer_persons", "responsible_persons"]
        for person_type in person_types:
            person_list = getattr(measure_task, person_type)
            if person_list:
                member = await _fetch_members(users_repository, person_list[0].name, sort_by, filters)
                if member:
                    measure_task_functions[measure_task.urn].append(member)
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
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.DELETE]})
async def delete_algorithm(
    request: Request,
    algorithm_id: int,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
) -> HTMLResponse:
    await algorithms_service.delete(algorithm_id)
    return templates.Redirect(request, "/algorithms/")


@router.get("/{algorithm_id}/measure/{measure_urn}")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
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
    filters: dict[str, str | list[str | int]],
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
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
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
    return templates.Redirect(request, f"/algorithm/{algorithm_id}/details/system_card/compliance")


@router.get("/{algorithm_id}/members")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
async def get_algorithm_members(
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
            Navigation.ALGORITHM_MEMBERS,
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

    return templates.TemplateResponse(request, "algorithms/members.html.j2", context)


@router.get("/{algorithm_id}/details/system_card/assessments/{assessment_card}")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
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

    editables = get_resolved_editables(context_variables={"algorithm_id": algorithm_id})

    context = {
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "assessment_card": assessment_card_data,
        "last_edited": algorithm.last_edited,
        "sub_menu_items": sub_menu_items,
        "breadcrumbs": breadcrumbs,
        "algorithm_id": algorithm.id,
        "editables": editables,
    }

    return templates.TemplateResponse(request, "pages/assessment_card.html.j2", context)


@router.get("/{algorithm_id}/details/system_card/models/{model_card}")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
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

    editables = get_resolved_editables(context_variables={"algorithm_id": algorithm_id})

    context = {
        "base_href": f"/algorithm/{ algorithm_id }",
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "model_card": model_card_data,
        "last_edited": algorithm.last_edited,
        "breadcrumbs": breadcrumbs,
        "algorithm": algorithm,
        "algorithm_id": algorithm.id,
        "tab_items": tab_items,
        "editables": editables,
    }

    return templates.TemplateResponse(request, "pages/model_card.html.j2", context)


@router.get("/{algorithm_id}/details/system_card/download")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
async def download_algorithm_system_card_as_yaml(
    algorithm_id: int, algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)], request: Request
) -> FileResponse:
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    filename = algorithm.name + "_" + datetime.datetime.now(datetime.UTC).isoformat() + ".yaml"
    with open(filename, "w") as outfile:
        yaml.dump(algorithm.system_card.model_dump(), outfile, sort_keys=False)
    try:
        return FileResponse(filename, filename=filename)
    except AMTRepositoryError as e:
        raise AMTNotFound from e


@router.get("/{algorithm_id}/file/{ulid}")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
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
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
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
