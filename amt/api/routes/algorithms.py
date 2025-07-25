import logging
from copy import deepcopy
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse

from amt.api.ai_act_profile import get_ai_act_profile_selector
from amt.api.decorators import permission
from amt.api.deps import get_request_permissions, templates
from amt.api.editable_route_utils import get_user_id_or_error
from amt.api.forms.algorithm import get_algorithm_form
from amt.api.group_by_category import get_localized_group_by_categories
from amt.api.lifecycles import Lifecycles, get_localized_lifecycle, get_localized_lifecycles
from amt.api.navigation import Navigation, resolve_base_navigation_items, resolve_navigation_items
from amt.api.risk_group import (
    get_localized_risk_groups,
)
from amt.api.routes.shared import get_filters_and_sort_by
from amt.core.authorization import AuthorizationResource, AuthorizationVerb, get_user
from amt.core.internationalization import get_current_translation
from amt.models import Algorithm
from amt.schema.algorithm import AlgorithmNew
from amt.schema.webform import WebForm
from amt.services.algorithms import AlgorithmsService, get_template_files
from amt.services.organizations import OrganizationsService
from amt.services.services_provider import ServicesProvider, get_service_provider
from amt.services.users import UsersService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
@permission({AuthorizationResource.ALGORITHMS: [AuthorizationVerb.LIST]})
async def get_root(
    request: Request,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, ge=1),  # todo: fix infinite scroll
    search: str = Query(""),
    display_type: str = Query(""),
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    users_service = await services_provider.get(UsersService)
    filters, drop_filters, localized_filters, sort_by = await get_filters_and_sort_by(request, users_service)

    filters["user_id"] = get_user_id_or_error(request)

    algorithms, amount_algorithm_systems = await get_algorithms(
        algorithms_service, display_type, filters, limit, request, search, skip, sort_by
    )
    next = skip + limit

    sub_menu_items = resolve_navigation_items([Navigation.ALGORITHMS_OVERVIEW], request)  # pyright: ignore [reportUnusedVariable] # noqa
    breadcrumbs = resolve_base_navigation_items([Navigation.ALGORITHMS_ROOT, Navigation.ALGORITHMS_OVERVIEW], request)

    context: dict[str, Any] = {
        "breadcrumbs": breadcrumbs,
        "sub_menu_items": {},  # sub_menu_items disabled for now
        "algorithms": algorithms,
        "amount_algorithm_systems": amount_algorithm_systems,
        "permission_path": AuthorizationResource.ALGORITHMS,
        "next": next,
        "limit": limit,
        "start": skip,
        "search": search,
        "lifecycles": get_localized_lifecycles(request),
        "risk_groups": get_localized_risk_groups(request),
        "group_by_categories": get_localized_group_by_categories(request),
        "filters": localized_filters,
        "sort_by": sort_by,
        "display_type": display_type,
        "base_href": "/algorithms/",
    }

    if request.state.htmx and drop_filters:
        return templates.TemplateResponse(request, "parts/algorithm_search.html.j2", context)
    elif request.state.htmx:
        return templates.TemplateResponse(request, "parts/filter_list.html.j2", context)
    else:
        return templates.TemplateResponse(request, "algorithms/index.html.j2", context)


async def get_algorithms(
    algorithms_service: AlgorithmsService,
    display_type: str,
    filters: dict[str, Any],
    limit: int,
    request: Request,
    search: str,
    skip: int,
    sort_by: dict[str, str],
) -> tuple[dict[str, list[Algorithm]], int | Any]:
    amount_algorithm_systems: int = 0

    if display_type == "LIFECYCLE":
        algorithms: dict[str, list[Algorithm]] = {}

        # When the lifecycle filter is active, only show these algorithms
        if "lifecycle" in filters:
            for lifecycle in Lifecycles:
                algorithms[lifecycle.name] = []
            algorithms[cast(str, filters["lifecycle"])] = await algorithms_service.paginate(
                skip=skip, limit=limit, search=search, filters=filters, sort=sort_by
            )
            amount_algorithm_systems += len(algorithms[cast(str, filters["lifecycle"])])
        else:
            for lifecycle in Lifecycles:
                filters["lifecycle"] = lifecycle.name
                algorithms[lifecycle.name] = await algorithms_service.paginate(
                    skip=skip, limit=limit, search=search, filters=filters, sort=sort_by
                )
                amount_algorithm_systems += len(algorithms[lifecycle.name])
    else:
        algorithms = await algorithms_service.paginate(
            skip=skip, limit=limit, search=search, filters=filters, sort=sort_by
        )  # pyright: ignore [reportAssignmentType]
        # todo: the lifecycle has to be 'localized', maybe for display 'Algorithm' should become a different object
        # fixme: detach algorithms from the database to prevent commits back by the auto-commit
        algorithms = deepcopy(algorithms)
        for algorithm in algorithms:
            algorithm.lifecycle = get_localized_lifecycle(algorithm.lifecycle, request)  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
        amount_algorithm_systems += len(algorithms)
    return algorithms, amount_algorithm_systems


@router.get("/new")
@permission({AuthorizationResource.ALGORITHMS: [AuthorizationVerb.CREATE]})
async def get_new(
    request: Request,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    organization_id: int = Query(None),
) -> HTMLResponse:
    organizations_service = await services_provider.get(OrganizationsService)
    sub_menu_items = resolve_navigation_items([Navigation.ALGORITHMS_OVERVIEW], request)  # pyright: ignore [reportUnusedVariable] # noqa
    breadcrumbs = resolve_base_navigation_items([Navigation.ALGORITHMS_ROOT, Navigation.ALGORITHM_NEW], request)

    # clean up session storage

    ai_act_profile = get_ai_act_profile_selector(request)

    user = get_user(request)

    request_permissions: dict[str, list[AuthorizationVerb]] = get_request_permissions(request)

    algorithm_form: WebForm = await get_algorithm_form(
        id="algorithm",
        translations=get_current_translation(request),
        organizations_service=organizations_service,
        user_id=user["sub"] if user else None,
        organization_id=organization_id,
        permissions=request_permissions,
    )

    template_files = get_template_files()

    context: dict[str, Any] = {
        "instruments": [],
        "ai_act_profile": ai_act_profile,
        "breadcrumbs": breadcrumbs,
        "sub_menu_items": {},  # sub_menu_items disabled for now,
        "lifecycles": get_localized_lifecycles(request),
        "template_files": template_files,
        "form": algorithm_form,
    }

    response = templates.TemplateResponse(request, "algorithms/new.html.j2", context)
    return response


@router.post("/new", response_class=HTMLResponse)
@permission({AuthorizationResource.ALGORITHMS: [AuthorizationVerb.CREATE]})
async def post_new(
    request: Request,
    algorithm_new: AlgorithmNew,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    user: dict[str, Any] | None = get_user(request)
    # TODO (Robbert): we need to handle (show) repository or service errors in the forms
    algorithm = await algorithms_service.create(algorithm_new, user["sub"])  # pyright: ignore[reportOptionalSubscript, reportUnknownArgumentType]
    response = templates.Redirect(request, f"/algorithm/{algorithm.id}/info")
    return response
