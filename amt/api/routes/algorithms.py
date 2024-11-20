import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse

from amt.api.ai_act_profile import get_ai_act_profile_selector
from amt.api.deps import templates
from amt.api.group_by_category import get_localized_group_by_categories
from amt.api.lifecycles import Lifecycles, get_localized_lifecycle, get_localized_lifecycles
from amt.api.navigation import Navigation, resolve_base_navigation_items, resolve_navigation_items
from amt.api.publication_category import (
    PublicationCategories,
    get_localized_publication_categories,
    get_localized_publication_category,
)
from amt.models import Algorithm
from amt.schema.algorithm import AlgorithmNew
from amt.schema.localized_value_item import LocalizedValueItem
from amt.services.algorithms import AlgorithmsService, get_template_files
from amt.services.instruments import InstrumentsService, create_instrument_service

router = APIRouter()
logger = logging.getLogger(__name__)


def get_localized_value(key: str, value: str, request: Request) -> LocalizedValueItem:
    match key:
        case "lifecycle":
            localized = get_localized_lifecycle(Lifecycles[value], request)
        case "publication-category":
            localized = get_localized_publication_category(PublicationCategories[value], request)
        case _:
            localized = None

    if localized:
        return localized

    return LocalizedValueItem(value=value, display_value="Unknown filter option")


@router.get("/")
async def get_root(
    request: Request,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, ge=1),  # todo: fix infinite scroll
    search: str = Query(""),
    display_type: str = Query(""),
) -> HTMLResponse:
    active_filters = {
        k.removeprefix("active-filter-"): v
        for k, v in request.query_params.items()
        if k.startswith("active-filter") and v != ""
    }
    add_filters = {
        k.removeprefix("add-filter-"): v
        for k, v in request.query_params.items()
        if k.startswith("add-filter") and v != ""
    }
    drop_filters = [v for k, v in request.query_params.items() if k.startswith("drop-filter") and v != ""]
    filters = {k: v for k, v in (active_filters | add_filters).items() if k not in drop_filters}
    localized_filters = {k: get_localized_value(k, v, request) for k, v in filters.items()}
    sort_by = {
        k.removeprefix("sort-by-"): v for k, v in request.query_params.items() if k.startswith("sort-by-") and v != ""
    }

    amount_algorithm_systems: int = 0
    if display_type == "LIFECYCLE":
        algorithms: dict[str, list[Algorithm]] = {}

        # When the lifecycle filter is active, only show these algorithms
        if "lifecycle" in filters:
            for lifecycle in Lifecycles:
                algorithms[lifecycle.name] = []
            algorithms[filters["lifecycle"]] = await algorithms_service.paginate(
                skip=skip, limit=limit, search=search, filters=filters, sort=sort_by
            )
            amount_algorithm_systems += len(algorithms[filters["lifecycle"]])
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
        for algorithm in algorithms:
            algorithm.lifecycle = get_localized_lifecycle(algorithm.lifecycle, request)  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
        amount_algorithm_systems += len(algorithms)
    next = skip + limit

    sub_menu_items = resolve_navigation_items([Navigation.ALGORITHMS_OVERVIEW], request)  # pyright: ignore [reportUnusedVariable] # noqa
    breadcrumbs = resolve_base_navigation_items([Navigation.ALGORITHMS_ROOT, Navigation.ALGORITHMS_OVERVIEW], request)

    context: dict[str, Any] = {
        "breadcrumbs": breadcrumbs,
        "sub_menu_items": {},  # sub_menu_items disabled for now
        "algorithms": algorithms,
        "amount_algorithm_systems": amount_algorithm_systems,
        "next": next,
        "limit": limit,
        "start": skip,
        "search": search,
        "lifecycles": get_localized_lifecycles(request),
        "publication_categories": get_localized_publication_categories(request),
        "group_by_categories": get_localized_group_by_categories(request),
        "filters": localized_filters,
        "sort_by": sort_by,
        "display_type": display_type,
    }

    if request.state.htmx and drop_filters:
        return templates.TemplateResponse(request, "parts/algorithm_search.html.j2", context)
    elif request.state.htmx:
        return templates.TemplateResponse(request, "parts/filter_list.html.j2", context)
    else:
        return templates.TemplateResponse(request, "algorithms/index.html.j2", context)


@router.get("/new")
async def get_new(
    request: Request,
    instrument_service: Annotated[InstrumentsService, Depends(create_instrument_service)],
) -> HTMLResponse:
    sub_menu_items = resolve_navigation_items([Navigation.ALGORITHMS_OVERVIEW], request)  # pyright: ignore [reportUnusedVariable] # noqa
    breadcrumbs = resolve_base_navigation_items([Navigation.ALGORITHMS_ROOT, Navigation.ALGORITHM_NEW], request)

    ai_act_profile = get_ai_act_profile_selector(request)

    template_files = get_template_files()

    instruments = await instrument_service.fetch_instruments()

    context: dict[str, Any] = {
        "instruments": instruments,
        "ai_act_profile": ai_act_profile,
        "breadcrumbs": breadcrumbs,
        "sub_menu_items": {},  # sub_menu_items disabled for now,
        "lifecycles": get_localized_lifecycles(request),
        "template_files": template_files,
    }

    response = templates.TemplateResponse(request, "algorithms/new.html.j2", context)
    return response


@router.post("/new", response_class=HTMLResponse)
async def post_new(
    request: Request,
    algorithm_new: AlgorithmNew,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
) -> HTMLResponse:
    algorithm = await algorithms_service.create(algorithm_new)
    response = templates.Redirect(request, f"/algorithm/{algorithm.id}/details/tasks")
    return response
