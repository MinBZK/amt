import datetime
import logging
import urllib.parse
from collections import defaultdict
from collections.abc import Sequence
from typing import Annotated, Any, cast
from uuid import UUID

import yaml
from fastapi import APIRouter, Depends, File, Form, Header, Query, Request, Response, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from ulid import ULID

from amt.api.decorators import permission
from amt.api.deps import templates
from amt.api.editable import (
    Editables,
    enrich_editable,
    find_matching_editable,
    get_resolved_editable,
    get_resolved_editables,
)
from amt.api.editable_classes import EditModes, ResolvedEditable
from amt.api.editable_enforcers import EditableEnforcerMustHaveMaintainer
from amt.api.editable_route_utils import create_editable_for_role, get_user_id_or_error, update_handler
from amt.api.forms.algorithm import get_algorithm_members_form
from amt.api.forms.measure import MeasureStatusOptions, get_measure_form
from amt.api.lifecycles import Lifecycles, get_localized_lifecycles
from amt.api.navigation import (
    BaseNavigationItem,
    Navigation,
    NavigationItem,
    resolve_base_navigation_items,
    resolve_navigation_items,
)
from amt.api.routes.shared import get_filters_and_sort_by, replace_none_with_empty_string_inplace
from amt.core.authorization import AuthorizationResource, AuthorizationType, AuthorizationVerb
from amt.core.exceptions import AMTError, AMTNotFound, AMTPermissionDenied, AMTRepositoryError
from amt.core.internationalization import get_current_translation
from amt.enums.tasks import Status, TaskType, life_cycle_mapper, measure_state_to_status, status_mapper
from amt.models import Algorithm, Authorization, User
from amt.models.task import Task
from amt.schema.localized_value_item import LocalizedValueItem
from amt.schema.measure import ExtendedMeasureTask, MeasureTask, Person
from amt.schema.measure_display import DisplayMeasureTask
from amt.schema.requirement import RequirementTask
from amt.schema.system_card import SystemCard
from amt.schema.task import DisplayTask, MovedTask
from amt.schema.user import User as UserSchema
from amt.services.algorithms import AlgorithmsService
from amt.services.authorization import AuthorizationsService
from amt.services.instruments_and_requirements_state import InstrumentStateService, RequirementsStateService
from amt.services.measures import measures_service
from amt.services.object_storage import ObjectStorageService, create_object_storage_service
from amt.services.organizations import OrganizationsService
from amt.services.requirements import requirements_service
from amt.services.services_provider import ServicesProvider, get_service_provider
from amt.services.tasks import TasksService
from amt.services.users import UsersService

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


def get_measure_task_or_error(system_card: SystemCard, measure_urn: str) -> MeasureTask:
    measure_task = find_measure_task(system_card, measure_urn)
    if not measure_task:
        raise AMTNotFound
    return measure_task


def get_algorithm_details_tabs(request: Request) -> list[NavigationItem]:
    return resolve_navigation_items(
        [
            Navigation.ALGORITHM_INFO,
            Navigation.ALGORITHM_DETAILS,
            Navigation.ALGORITHM_COMPLIANCE,
            Navigation.ALGORITHM_TASKS,
            Navigation.ALGORITHM_MEMBERS,
        ],
        request,
    )


def get_algorithms_submenu_items() -> list[BaseNavigationItem]:
    return [Navigation.ALGORITHMS_OVERVIEW, Navigation.ALGORITHM_TASKS]


@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
@router.get("/{algorithm_id}/tasks")
async def get_tasks(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    search: str = Query(""),
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    users_service = await services_provider.get(UsersService)
    authorizations_service = await services_provider.get(AuthorizationsService)
    tasks_service = await services_provider.get(TasksService)

    filters, drop_filters, localized_filters, _ = await get_filters_and_sort_by(request, users_service)
    if search:
        filters["search"] = search

    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)

    tab_items = get_algorithm_details_tabs(request)

    tasks_db: Sequence[Task] = await tasks_service.get_tasks_for_algorithm(algorithm_id, None)

    # resolve measure tasks
    urns: set[str] = {task.type_id for task in tasks_db if task.type == TaskType.MEASURE and task.type_id is not None}
    resolved_measures: dict[str, DisplayMeasureTask] = (
        {} if len(urns) == 0 else await resolve_and_enrich_measures(algorithm, urns, users_service)
    )

    def filters_match(display_task: DisplayTask) -> bool:
        if len(filters) == 0:
            return True
        return all(
            (
                (
                    "assignee" not in filters
                    or any(
                        str(user.id) == filters.get("assignee")
                        for user in display_task.type_object.users  # pyright: ignore[reportOptionalMemberAccess]
                        if "assignee" in filters and display_task.type_object is not None
                    )
                ),
                (
                    "lifecycle" not in filters
                    or any(
                        lifecycle == life_cycle_mapper[Lifecycles(filters.get("lifecycle"))]
                        for lifecycle in display_task.type_object.lifecycle  # pyright: ignore[reportOptionalMemberAccess]
                        if "lifecycle" in filters and display_task.type_object is not None
                    )
                ),
                (
                    "search" not in filters
                    or (
                        "search" in filters
                        and display_task.type_object is not None
                        and (
                            cast(str, filters["search"]).casefold() in display_task.type_object.name.casefold()  # pyright: ignore[reportOptionalMemberAccess]
                            or cast(str, filters["search"]).casefold()
                            in display_task.type_object.description.casefold()  # pyright: ignore[reportOptionalMemberAccess]
                        )
                    )
                ),
            )
        )

    tasks_by_status: dict[Status, list[DisplayTask]] = {}
    for status in Status:
        tasks_by_status[status] = []
        all_tasks = [
            # we create display task for Measures,
            #  this could be extended in the future to support other types
            DisplayTask.create_from_model(task, resolved_measures.get(task.type_id))
            for task in tasks_db
            if task.status_id == status and task.type == TaskType.MEASURE and task.type_id is not None
        ]
        tasks_by_status[status] = [task for task in all_tasks if filters_match(task)]
        # we also append all tasks that have no related object
        tasks_by_status[status] += [
            DisplayTask.create_from_model(task, None)
            for task in tasks_db
            if task.status_id == status and task.type is None
        ]

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details"),
            Navigation.ALGORITHM_TASKS,
        ],
        request,
    )

    members = await get_algorithm_members(algorithm, authorizations_service)

    context = {
        "tasks_by_status": tasks_by_status,
        "permission_path": AuthorizationResource.ALGORITHM_SYSTEMCARD.format_map({"algorithm_id": algorithm.id}),
        "statuses": Status,
        "algorithm": algorithm,
        "algorithm_id": algorithm.id,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
        "base_href": f"/algorithm/{algorithm_id}/tasks",
        "search": search,
        "lifecycles": get_localized_lifecycles(request),
        "assignees": [LocalizedValueItem(value=str(member.id), display_value=member.name) for member in members],
        "filters": localized_filters,
    }

    headers = {"HX-Replace-Url": request.url.path + "?" + request.url.query}

    if request.state.htmx and drop_filters:
        return templates.TemplateResponse(request, "parts/tasks_search.html.j2", context, headers=headers)
    elif request.state.htmx:
        return templates.TemplateResponse(request, "parts/tasks_board.html.j2", context, headers=headers)
    else:
        return templates.TemplateResponse(request, "algorithms/tasks.html.j2", context, headers=headers)


async def get_algorithm_members(algorithm: Algorithm, authorizations_service: AuthorizationsService) -> list[User]:
    return [
        user
        for user, _, _, _ in await authorizations_service.find_all(
            filters={"type": AuthorizationType.ALGORITHM, "type_id": algorithm.id}
        )
    ]


async def resolve_and_enrich_measures(
    algorithm: Algorithm, urns: set[str], users_service: UsersService
) -> dict[str, DisplayMeasureTask]:
    """
    Using the given algorithm and list of measure urns, retrieve all those measures
    and combine the information from the task registry with the system card information
    and return it.
    :param algorithm: the algorithm
    :param urns: the list of measure urns
    :param users_service: the user service
    :return: a list of enriched measure tasks
    """
    enriched_resolved_measures: dict[str, DisplayMeasureTask] = {}
    resolved_measures = await measures_service.fetch_measures(list(urns))
    for resolved_measure in resolved_measures:
        system_measure = find_measure_task(algorithm.system_card, resolved_measure.urn)
        if system_measure is not None and system_measure.urn not in enriched_resolved_measures:
            all_users: list[UserSchema] = []
            for person_type in ["responsible_persons", "reviewer_persons", "accountable_persons"]:
                persons = getattr(system_measure, person_type, [])
                for person in persons if persons is not None else []:
                    user = UserSchema.create_from_model(await users_service.find_by_id(person.uuid))
                    if user is not None:
                        all_users.append(user)
            measure_task_display = DisplayMeasureTask(
                name=resolved_measure.name,
                description=resolved_measure.description,
                urn=resolved_measure.urn,
                state=system_measure.state,
                value=system_measure.value,
                version=system_measure.version,
                users=all_users,
                lifecycle=resolved_measure.lifecycle,
            )
            enriched_resolved_measures[system_measure.urn] = measure_task_display
    return enriched_resolved_measures


@router.patch("/{algorithm_id}/move_task")
@permission({AuthorizationResource.ALGORITHM_SYSTEMCARD: [AuthorizationVerb.UPDATE]})
async def move_task(
    request: Request,
    algorithm_id: int,
    moved_task: MovedTask,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    users_service = await services_provider.get(UsersService)
    tasks_service = await services_provider.get(TasksService)
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

    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)

    if task.type == TaskType.MEASURE and task.type_id is not None:
        measure_task = get_measure_task_or_error(algorithm.system_card, task.type_id)
        measure_task.update(state=status_mapper[Status(moved_task.status_id)])

        await update_requirements_state(algorithm, measure_task.urn)

        await algorithms_service.update(algorithm)

        unique_resolved_measures: dict[str, DisplayMeasureTask] = await resolve_and_enrich_measures(
            algorithm, {measure_task.urn}, users_service
        )
        resolved_measure: DisplayMeasureTask | None = unique_resolved_measures.get(measure_task.urn)
        if resolved_measure is None:
            raise AMTError(f"No measure found for {measure_task.urn}")

        display_task: DisplayTask = DisplayTask.create_from_model(task, resolved_measure)
    else:
        display_task: DisplayTask = DisplayTask.create_from_model(task)

    context: dict[str, Any] = {
        "algorithm_id": algorithm_id,
        "permission_path": AuthorizationResource.ALGORITHM_SYSTEMCARD.format_map({"algorithm_id": algorithm_id}),
        "task": display_task,
        "request": request,
    }

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


@router.get("/{algorithm_id}")
async def get_algorithm_details_redirect(
    algorithm_id: int,
) -> RedirectResponse:
    return RedirectResponse(url=f"/algorithm/{algorithm_id}/info")


@router.get("/{algorithm_id}/info")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
async def get_algorithm_details(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm, context = await get_algorithm_context(algorithm_id, algorithms_service, request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details"),
            Navigation.ALGORITHM_INFO,
        ],
        request,
    )

    context.update(
        {
            "breadcrumbs": breadcrumbs,
            "base_href": f"/algorithm/{algorithm_id}",
            "editables": get_resolved_editables(context_variables={"algorithm_id": algorithm_id}),
        }
    )

    return templates.TemplateResponse(request, "algorithms/details_info.html.j2", context)


# TODO: permissions are now checked on the route path, but updates are done on the GET parameter
@router.get("/{algorithm_id}/edit")
@permission({AuthorizationResource.ALGORITHM_SYSTEMCARD: [AuthorizationVerb.UPDATE]})
async def get_algorithm_edit(
    request: Request,
    algorithm_id: int,
    full_resource_path: str,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    # TODO FIXME: this is too much of a hack! Find a better way
    request.state.authorization_type = AuthorizationType.ALGORITHM
    user_id = get_user_id_or_error(request)
    context_variables: dict[str, str | int] = {}
    matched_editable, extracted_context_variables = find_matching_editable(full_resource_path)
    context_variables.update(extracted_context_variables)
    resolved_editable = get_resolved_editable(matched_editable, context_variables, False)
    editable = await enrich_editable(
        resolved_editable, EditModes.EDIT, {"user_id": user_id}, services_provider, request, None
    )

    context = {
        "base_href": f"/algorithm/{algorithm_id}",
        "editable_object": editable,
    }

    return templates.TemplateResponse(request, "parts/edit_cell.html.j2", context)


@router.get("/{algorithm_id}/cancel")
@permission({AuthorizationResource.ALGORITHM_SYSTEMCARD: [AuthorizationVerb.UPDATE]})
async def get_algorithm_cancel(
    request: Request,
    algorithm_id: int,
    full_resource_path: str,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    user_id = get_user_id_or_error(request)
    context_variables: dict[str, Any] = {"algorithm_id": algorithm_id}
    matched_editable, extracted_context_variables = find_matching_editable(full_resource_path)
    context_variables.update(extracted_context_variables)
    resolved_editable = get_resolved_editable(matched_editable, context_variables, False)
    editable = await enrich_editable(
        resolved_editable, EditModes.VIEW, {"user_id": user_id}, services_provider, request, None
    )

    context = {
        "relative_resource_path": editable.relative_resource_path if editable.relative_resource_path else "",
        # TODO: SET PERMISSION FOR EACH EDITABLE!!
        "has_permission": True,
        "base_href": f"/algorithm/{algorithm_id}",
        "resource_object": editable.resource_object,
        "full_resource_path": full_resource_path,
        "editable_object": editable,
        "editables": get_resolved_editables(context_variables={"algorithm_id": algorithm_id}),
    }

    return templates.TemplateResponse(request, "parts/view_cell.html.j2", context)


@router.put("/{algorithm_id}/update")
@permission({AuthorizationResource.ALGORITHM_SYSTEMCARD: [AuthorizationVerb.UPDATE]})
async def get_algorithm_update(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    full_resource_path: str = Query(""),
    current_state_str: str = Header("VALIDATE", alias="X-Current-State"),
) -> HTMLResponse:
    context_variables: dict[str, str | int] = {"algorithm_id": algorithm_id}
    base_href = f"/algorithm/{algorithm_id}"

    return await update_handler(
        request,
        full_resource_path,
        base_href,
        current_state_str,
        context_variables,
        EditModes.SAVE,
        services_provider,
    )


@router.get("/{algorithm_id}/details")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
async def get_system_card(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)

    editables = get_resolved_editables(context_variables={"algorithm_id": algorithm_id})

    tab_items = get_algorithm_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details"),
            Navigation.ALGORITHM_DETAILS,
        ],
        request,
    )

    system_card = algorithm.system_card
    replace_none_with_empty_string_inplace(system_card)

    context = {
        "system_card": system_card,
        "permission_path": AuthorizationResource.ALGORITHM_SYSTEMCARD.format_map({"algorithm_id": algorithm.id}),
        "instrument_state": instrument_state,
        "requirements_state": requirements_state,
        "last_edited": algorithm.last_edited,
        "algorithm": algorithm,
        "algorithm_id": algorithm.id,
        "tab_items": tab_items,
        "breadcrumbs": breadcrumbs,
        "editables": editables,
        "base_href": f"/algorithm/{algorithm_id}",
    }

    return templates.TemplateResponse(request, "pages/system_card.html.j2", context)


@router.get("/{algorithm_id}/compliance")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
async def get_system_card_requirements(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    organizations_service = await services_provider.get(OrganizationsService)
    users_service = await services_provider.get(UsersService)
    algorithms_service = await services_provider.get(AlgorithmsService)

    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)
    tab_items = get_algorithm_details_tabs(request)
    filters, _, _, _ = await get_filters_and_sort_by(request, users_service)
    organization = await organizations_service.get_by_id(algorithm.organization_id)  # pyright: ignore [reportUnknownMemberType]
    filters["organization-id"] = str(organization.id)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details"),
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

    measure_task_functions: dict[str, list[User]] = await get_measure_task_functions(measure_tasks, users_service)

    context = {
        "permission_path": AuthorizationResource.ALGORITHM_SYSTEMCARD.format_map({"algorithm_id": algorithm.id}),
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


async def get_measure_task_functions(
    measure_tasks: list[MeasureTask],
    users_service: Annotated[UsersService, Depends(UsersService)],
) -> dict[str, list[User]]:
    measure_task_functions: dict[str, list[User]] = defaultdict(list)

    for measure_task in measure_tasks:
        person_types = ["responsible_persons", "reviewer_persons", "accountable_persons"]
        for person_type in person_types:
            person_list = getattr(measure_task, person_type)
            if person_list:
                member = await users_service.find_by_id(person_list[0].uuid)
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
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    await algorithms_service.delete(algorithm_id)
    return templates.Redirect(request, "/algorithms/")


@router.get("/{algorithm_id}/measure/{measure_urn}")
@permission({AuthorizationResource.ALGORITHM_SYSTEMCARD: [AuthorizationVerb.UPDATE]})
async def get_measure(
    request: Request,
    algorithm_id: int,
    measure_urn: str,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    object_storage_service: Annotated[ObjectStorageService, Depends(create_object_storage_service)],
    search: str = Query(""),
    requirement_urn: str = "",
) -> HTMLResponse:
    users_service = await services_provider.get(UsersService)
    authorizations_service = await services_provider.get(AuthorizationsService)
    algorithms_service = await services_provider.get(AlgorithmsService)

    filters, _, _, sort_by = await get_filters_and_sort_by(request, users_service)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    measure = await measures_service.fetch_measures([measure_urn])
    measure_task = get_measure_task_or_error(algorithm.system_card, measure_urn)

    filenames: list[tuple[str, str]] = []
    for file in measure_task.files:
        metadata = object_storage_service.get_file_metadata_from_object_name(file)
        filenames.append((file.split("/")[-1], f"{metadata.filename}.{metadata.ext}"))

    filters.update({"type": AuthorizationType.ALGORITHM, "type_id": algorithm.id})
    members = [
        user for user, _, _, _ in await authorizations_service.find_all(search=search, sort=sort_by, filters=filters)
    ]

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

    context = {
        "measure": measure[0],
        "algorithm_id": algorithm_id,
        "form": measure_form,
        "requirement_urn": requirement_urn,
    }

    return templates.TemplateResponse(request, "algorithms/details_measure_modal.html.j2", context)


async def get_users_from_function_name(
    measure_accountable: Annotated[str | None, Form()],
    measure_reviewer: Annotated[str | None, Form()],
    measure_responsible: Annotated[str | None, Form()],
    users_service: Annotated[UsersService, Depends(UsersService)],
    sort_by: dict[str, str],
    filters: dict[str, str | list[str | int]],
) -> tuple[list[Person], list[Person], list[Person]]:
    accountable_persons, reviewer_persons, responsible_persons = [], [], []
    # TODO: the user link must be done differently, search by name is going to give problems!!
    if measure_accountable:
        accountable_member = await users_service.find_all(search=measure_accountable, sort=sort_by, filters=filters)  # pyright: ignore[reportDeprecated]
        accountable_persons = [Person(name=accountable_member[0].name, uuid=str(accountable_member[0].id))]  # pyright: ignore [reportOptionalMemberAccess]
    if measure_reviewer:
        reviewer_member = await users_service.find_all(search=measure_reviewer, sort=sort_by, filters=filters)  # pyright: ignore[reportDeprecated]
        reviewer_persons = [Person(name=reviewer_member[0].name, uuid=str(reviewer_member[0].id))]  # pyright: ignore [reportOptionalMemberAccess]
    if measure_responsible:
        responsible_member = await users_service.find_all(search=measure_responsible, sort=sort_by, filters=filters)  # pyright: ignore[reportDeprecated]
        responsible_persons = [Person(name=responsible_member[0].name, uuid=str(responsible_member[0].id))]  # pyright: ignore [reportOptionalMemberAccess]
    return accountable_persons, reviewer_persons, responsible_persons


@router.post("/{algorithm_id}/measure/{measure_urn}")
@permission({AuthorizationResource.ALGORITHM_SYSTEMCARD: [AuthorizationVerb.UPDATE]})
async def update_measure_value(
    request: Request,
    algorithm_id: int,
    measure_urn: str,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    object_storage_service: Annotated[ObjectStorageService, Depends(create_object_storage_service)],
    measure_state: Annotated[str, Form()],
    measure_responsible: Annotated[str | None, Form()] = None,
    measure_reviewer: Annotated[str | None, Form()] = None,
    measure_accountable: Annotated[str | None, Form()] = None,
    measure_value: Annotated[str | None, Form()] = None,
    measure_links: Annotated[list[str] | None, Form()] = None,
    measure_files: Annotated[list[UploadFile] | None, File()] = None,
    requirement_urn: str = "",
) -> HTMLResponse:
    tasks_service = await services_provider.get(TasksService)
    users_service = await services_provider.get(UsersService)
    algorithms_service = await services_provider.get(AlgorithmsService)

    filters, _, _, sort_by = await get_filters_and_sort_by(request, users_service)
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
        measure_accountable,
        measure_reviewer,
        measure_responsible,
        users_service,
        sort_by,
        filters,  # pyright: ignore[reportArgumentType]
    )

    measure_task.update(
        measure_state, measure_value, measure_links, paths, responsible_persons, accountable_persons, reviewer_persons
    )

    # update the tasks
    await tasks_service.update_tasks_status(
        algorithm_id, TaskType.MEASURE, measure_task.urn, measure_state_to_status(measure_task.state)
    )

    await update_requirements_state(algorithm, measure_urn)

    await algorithms_service.update(algorithm)

    # the redirect 'to same page' does not trigger a javascript reload, so we let us redirect by a different server URL
    encoded_url = urllib.parse.quote_plus(f"/algorithm/{algorithm_id}/compliance#{requirement_urn.replace(':', '_')}")
    referer = urllib.parse.urlparse(request.headers.get("referer", ""))

    if referer.path.endswith("/tasks"):
        encoded_url = urllib.parse.quote_plus(referer.path + "?" + referer.query)
    return templates.Redirect(
        request,
        f"/algorithm/{algorithm_id}/redirect?to={encoded_url}",
    )


async def update_requirements_state(algorithm: Algorithm, measure_urn: str) -> Algorithm:
    """
    Update the state of requirements depending on the given measure. Note this method does not save the algorithm
    but returns the updated algorithm.
    :param algorithm: the algorithm to update
    :param measure_urn: the measure urn
    :return: the updated algorithm
    """
    # update for the linked requirements the state based on all it's measures
    requirement_tasks = await find_requirement_tasks_by_measure_urn(algorithm.system_card, measure_urn)
    requirement_urns = [requirement_task.urn for requirement_task in requirement_tasks]
    requirements = await requirements_service.fetch_requirements(requirement_urns)
    state_order_list = set(MeasureStatusOptions)
    for requirement in requirements:
        state_count: dict[str, int] = {}
        for link_measure_urn in requirement.links:
            link_measure_task = find_measure_task(algorithm.system_card, link_measure_urn)
            if link_measure_task:
                state_count[link_measure_task.state] = state_count.get(link_measure_task.state, 0) + 1
        requirement_task = find_requirement_task(algorithm.system_card, requirement.urn)
        full_match = False
        for state in state_order_list:
            # if all measures are in the same state, the requirement is set to that state
            if requirement_task and state_count.get(state, 0) == len(requirement.links):
                requirement_task.state = state
                full_match = True
                break
        # a requirement is considered 'in progress' if any measure is of any state other than todo
        if requirement_task and not full_match:
            if len([key for key in state_count if key != MeasureStatusOptions.TODO]) > 0:
                requirement_task.state = MeasureStatusOptions.IN_PROGRESS
            else:
                requirement_task.state = MeasureStatusOptions.TODO
    return algorithm


@router.get("/{algorithm_id}/redirect")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
async def redirect_to(request: Request, algorithm_id: str, to: str) -> RedirectResponse:
    """
    Redirects to the requested URL. We only have and use this because HTMX and javascript redirects do
    not work when redirecting to the same URL, even if query params are changed.
    """

    if not to.startswith("/"):
        raise AMTPermissionDenied

    return RedirectResponse(  # NOSONAR
        status_code=302,  # NOSONAR
        url=to,  # NOSONAR
    )  # NOSONAR


@router.get("/{algorithm_id}/details/system_card/assessments/{assessment_card}")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
async def get_assessment_card(
    request: Request,
    algorithm_id: int,
    assessment_card: str,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)

    request.state.path_variables.update({"assessment_card": assessment_card})

    sub_menu_items = resolve_navigation_items(get_algorithms_submenu_items(), request, False)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details"),
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
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    request.state.path_variables.update({"model_card": model_card})
    instrument_state = await get_instrument_state(algorithm.system_card)
    requirements_state = await get_requirements_state(algorithm.system_card)

    tab_items = get_algorithm_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details"),
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
        "base_href": f"/algorithm/{algorithm_id}",
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


@router.get("/{algorithm_id}/download")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
async def download_algorithm_system_card_as_yaml(
    algorithm_id: int,
    request: Request,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> Response:
    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)

    # Create YAML content in memory
    yaml_content = yaml.dump(algorithm.system_card.model_dump(), sort_keys=False)
    filename = algorithm.name + "_" + datetime.datetime.now(datetime.UTC).isoformat() + ".yaml"

    # Return the YAML content directly without saving to disk
    return Response(
        content=yaml_content,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/yaml; charset=utf-8",
        },
    )


@router.get("/{algorithm_id}/file/{ulid}")
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.READ]})
async def get_file(
    request: Request,
    algorithm_id: int,
    ulid: ULID,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    object_storage_service: Annotated[ObjectStorageService, Depends(create_object_storage_service)],
) -> Response:
    algorithms_service = await services_provider.get(AlgorithmsService)
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
@permission({AuthorizationResource.ALGORITHM_SYSTEMCARD: [AuthorizationVerb.UPDATE]})
async def delete_file(
    request: Request,
    algorithm_id: int,
    ulid: ULID,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    object_storage_service: Annotated[ObjectStorageService, Depends(create_object_storage_service)],
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    metadata = object_storage_service.get_file_metadata(algorithm.organization_id, algorithm_id, ulid)
    measure_task = get_measure_task_or_error(algorithm.system_card, metadata.measure_urn)

    entry_to_delete = object_storage_service.delete_file(algorithm.organization_id, algorithm_id, ulid)
    measure_task.files.remove(entry_to_delete)
    await algorithms_service.update(algorithm)

    return HTMLResponse(content="", status_code=200)


@router.get("/{algorithm_id}/members")
@permission({AuthorizationResource.ALGORITHM_MEMBER: [AuthorizationVerb.READ]})
async def get_members(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, ge=1),  # todo: fix infinite scroll
    search: str = Query(""),
) -> HTMLResponse:
    request.state.services_provider = services_provider
    authorizations_service = await services_provider.get(AuthorizationsService)
    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    users_service = await services_provider.get(UsersService)
    filters, drop_filters, localized_filters, sort_by = await get_filters_and_sort_by(request, users_service)
    tab_items = get_algorithm_details_tabs(request)
    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(custom_display_text=algorithm.name, url="/algorithm/{algorithm_id}/details"),
            Navigation.ALGORITHM_MEMBERS,
        ],
        request,
    )
    if "name" not in sort_by:
        sort_by["name"] = "ascending"

    filters: dict[str, int | str | list[str | int]] = {"type": AuthorizationType.ALGORITHM, "type_id": algorithm.id}
    members = await authorizations_service.find_all(search, sort_by, filters, skip, limit)

    context: dict[str, Any] = {
        "base_href": f"/algorithm/{algorithm.id}",
        "permission_path": AuthorizationResource.ALGORITHM_MEMBER.format_map({"algorithm_id": algorithm.id}),
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
        "members": members,
        "next": next,
        "limit": limit,
        "start": skip,
        "search": search,
        "sort_by": sort_by,
        "members_length": len(members),
        "filters": localized_filters,
        "include_filters": False,
        "algorithm": algorithm,
    }

    if request.state.htmx:
        if drop_filters:
            context.update({"include_filters": True})
        return templates.TemplateResponse(request, "organizations/parts/members_results.html.j2", context)
    else:
        context.update({"include_filters": True})
        return templates.TemplateResponse(request, "organizations/members.html.j2", context)


@router.get("/{algorithm_id}/members/form")
@permission({AuthorizationResource.ALGORITHM_MEMBER: [AuthorizationVerb.UPDATE]})
async def get_members_form(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    form = await get_algorithm_members_form(
        id="algorithm",
        translations=get_current_translation(request),
        algorithm=algorithm,
    )
    context: dict[str, Any] = {
        "form": form,
        "base_href": f"/algorithm/{algorithm.id}",
    }
    return templates.TemplateResponse(request, "organizations/parts/add_members_modal.html.j2", context)


@router.get("/{algorithm_id}/users")
async def get_users(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> Response:
    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    authorizations_service = await services_provider.get(AuthorizationsService)
    query = request.query_params.get("query", None)
    return_type = request.query_params.get("returnType", "json")
    filters: dict[str, int | str | list[str | int]] = {
        "type": AuthorizationType.ORGANIZATION,
        "type_id": algorithm.organization_id,
    }
    search_results = await authorizations_service.find_all(search=query, filters=filters, limit=25)

    match return_type:
        case "search_select_field":
            editables: list[ResolvedEditable] = []
            for user, _, _, _ in search_results:
                enriched_editable = await create_editable_for_role(
                    request,
                    services_provider,
                    user,
                    AuthorizationType.ALGORITHM,
                    algorithm.id,
                    (await authorizations_service.get_role("Algorithm Member")).id,
                )
                editables.append(enriched_editable)
            context = {"editables": editables, "show_no_results": len(search_results) == 0}
            return templates.TemplateResponse(request, "organizations/parts/search_select_field.html.j2", context)
        case _:
            return JSONResponse(content=search_results)


@router.put("/{algorithm_id}/members", response_class=HTMLResponse)
@permission({AuthorizationResource.ALGORITHM_MEMBER: [AuthorizationVerb.UPDATE]})
async def add_new_members(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    current_state_str: str = Header("VALIDATE", alias="X-Current-State"),
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)

    context_variables: dict[str, Any] = {
        "algorithm": algorithm,
    }

    return await update_handler(
        request,
        "authorization",
        f"/{algorithm_id}/members",
        current_state_str,
        context_variables,
        EditModes.SAVE_NEW,
        services_provider,
    )


@router.delete("/{algorithm_id}/members/{user_id}", response_class=HTMLResponse)
@permission({AuthorizationResource.ALGORITHM_MEMBER: [AuthorizationVerb.UPDATE]})
async def remove_member(
    request: Request,
    algorithm_id: int,
    user_id: UUID,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    authorizations_service = await services_provider.get(AuthorizationsService)
    users_service = await services_provider.get(UsersService)
    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)

    user: User | None = await users_service.find_by_id(user_id)
    if user is None:
        raise AMTNotFound()
    authorization = await authorizations_service.find_by_user_and_type(
        user.id, algorithm.id, AuthorizationType.ALGORITHM
    )

    editable_context = {
        "algorithm_id": algorithm.id,
        "authorization_id": authorization.id,
        "new_values": {"role_id": "0"},
    }
    resolved_editable = get_resolved_editable(Editables.AUTHORIZATION_ROLE, editable_context, False)
    resolved_editable.resource_object = Authorization(user_id=user.id)
    # TODO: this is a work-around and not very user-friendly, but ok for now
    await EditableEnforcerMustHaveMaintainer().enforce(
        request,
        resolved_editable,
        editable_context,
        EditModes.DELETE,
        services_provider,
    )
    await authorizations_service.remove_algorithm_roles(user_id, algorithm)
    return templates.Redirect(request, f"/algorithm/{algorithm_id}/members")
