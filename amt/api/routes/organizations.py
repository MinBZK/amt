from collections.abc import Sequence
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from amt.api.decorators import permission
from amt.api.deps import templates
from amt.api.editable import (
    Editables,
    get_enriched_resolved_editable,
    save_editable,
)
from amt.api.editable_classes import EditModes, ResolvedEditable
from amt.api.forms.organization import get_organization_form
from amt.api.group_by_category import get_localized_group_by_categories
from amt.api.lifecycles import get_localized_lifecycles
from amt.api.navigation import (
    BaseNavigationItem,
    Navigation,
    NavigationItem,
    resolve_base_navigation_items,
    resolve_navigation_items,
)
from amt.api.organization_filter_options import OrganizationFilterOptions, get_localized_organization_filters
from amt.api.risk_group import get_localized_risk_groups
from amt.api.routes.algorithm import get_user_id_or_error
from amt.api.routes.algorithms import get_algorithms
from amt.api.routes.shared import get_filters_and_sort_by
from amt.api.utils import SafeDict
from amt.core.authorization import AuthorizationResource, AuthorizationVerb, get_user
from amt.core.exceptions import AMTAuthorizationError, AMTNotFound, AMTRepositoryError
from amt.core.internationalization import get_current_translation
from amt.models import Organization, User
from amt.repositories.organizations import OrganizationsRepository
from amt.repositories.users import UsersRepository
from amt.schema.organization import OrganizationNew, OrganizationUsers
from amt.services.algorithms import AlgorithmsService
from amt.services.organizations import OrganizationsService
from amt.services.users import UsersService

router = APIRouter()


def get_organization_tabs(request: Request, organization_slug: str) -> list[NavigationItem]:
    request.state.path_variables = {"organization_slug": organization_slug}

    return resolve_navigation_items(
        [Navigation.ORGANIZATIONS_INFO, Navigation.ORGANIZATIONS_ALGORITHMS, Navigation.ORGANIZATIONS_MEMBERS],
        request,
    )


# TODO (Robbert): maybe this should become its own endpoint
@router.get("/users")
async def get_users(
    request: Request,
    users_repository: Annotated[UsersRepository, Depends(UsersRepository)],
) -> Response:
    query = request.query_params.get("query", None)
    return_type = request.query_params.get("returnType", "json")
    search_results = []
    if query and len(query) >= 2:
        search_results: list[dict[str, str | UUID]] = [
            {"value": str(user.id), "display_value": user.name}
            for user in await users_repository.find_all(search=query, limit=5)
        ]
    match return_type:
        case "search_select_field":
            context = {"search_results": search_results}
            return templates.TemplateResponse(request, "organizations/parts/search_select_field.html.j2", context)
        case _:
            return JSONResponse(content=search_results)


@router.get("/new")
async def get_new(
    request: Request,
    users_repository: Annotated[UsersRepository, Depends(UsersRepository)],
) -> HTMLResponse:
    breadcrumbs = resolve_base_navigation_items([Navigation.ORGANIZATIONS_ROOT, Navigation.ORGANIZATIONS_NEW], request)
    # todo (Robbert): make object SessionUser so it can be used as alternative for Database User
    session_user = get_user(request)
    if session_user:
        user = await users_repository.find_by_id(session_user["sub"])
        form = get_organization_form(id="organization", translations=get_current_translation(request), user=user)
        context: dict[str, Any] = {"form": form, "breadcrumbs": breadcrumbs}
        return templates.TemplateResponse(request, "organizations/new.html.j2", context)
    raise AMTAuthorizationError()


@router.get("/")
@permission({AuthorizationResource.ORGANIZATIONS: [AuthorizationVerb.LIST]})
async def root(
    request: Request,
    organizations_repository: Annotated[OrganizationsRepository, Depends(OrganizationsRepository)],
    users_service: Annotated[UsersService, Depends(UsersService)],
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, ge=1),  # todo: fix infinite scroll
    search: str = Query(""),
) -> HTMLResponse:
    filters, drop_filters, localized_filters, sort_by = await get_filters_and_sort_by(request, users_service)

    user = get_user(request)

    breadcrumbs = resolve_base_navigation_items(
        [Navigation.ORGANIZATIONS_ROOT, Navigation.ORGANIZATIONS_OVERVIEW], request
    )
    # TODO: we only show organizations you are a member of (request for the pilots)
    filters = {"organization-type": OrganizationFilterOptions.MY_ORGANIZATIONS.value}
    organizations: Sequence[Organization] = await organizations_repository.find_by(
        search=search, sort=sort_by, filters=filters, user_id=user["sub"] if user else None
    )
    # TODO: we remove the organization filter again, otherwise it shows up as 'filter option you can remove'
    localized_filters.pop("organization-type", None)

    # we only can show organization you belong to, so the all organizations option is disabled
    organization_filters = [
        f for f in get_localized_organization_filters(request) if f and f.value != OrganizationFilterOptions.ALL.value
    ]

    context: dict[str, Any] = {
        "breadcrumbs": breadcrumbs,
        "organizations": organizations,
        "next": next,
        "limit": limit,
        "start": skip,
        "search": search,
        "sort_by": sort_by,
        "organizations_length": len(organizations),
        "filters": localized_filters,
        "include_filters": False,
        "organization_filters": organization_filters,
    }

    if request.state.htmx:
        if drop_filters:
            context.update({"include_filters": True})
        return templates.TemplateResponse(request, "organizations/parts/overview_results.html.j2", context)
    else:
        context.update({"include_filters": True})
        return templates.TemplateResponse(request, "organizations/index.html.j2", context)


@router.post("/new", response_class=HTMLResponse)
@permission({AuthorizationResource.ORGANIZATIONS: [AuthorizationVerb.CREATE]})
async def post_new(
    request: Request,
    organization_new: OrganizationNew,
    organizations_service: Annotated[OrganizationsService, Depends(OrganizationsService)],
) -> HTMLResponse:
    session_user = get_user(request)

    await organizations_service.save(
        name=organization_new.name,
        slug=organization_new.slug,
        user_ids=organization_new.user_ids,  # pyright: ignore[reportArgumentType]
        created_by_user_id=(session_user["sub"] if session_user else None),  # pyright: ignore[reportUnknownArgumentType]
    )

    response = templates.Redirect(request, f"/organizations/{organization_new.slug}")
    return response


@router.get("/{organization_slug}")
@permission({AuthorizationResource.ORGANIZATION_INFO_SLUG: [AuthorizationVerb.READ]})
async def get_by_slug(
    request: Request,
    organization_slug: str,
    organizations_service: Annotated[OrganizationsService, Depends(OrganizationsService)],
) -> HTMLResponse:
    organization = await get_organization_or_error(organizations_service, request, organization_slug)
    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ORGANIZATIONS_ROOT,
            BaseNavigationItem(custom_display_text=organization.name, url="/organizations/{organization_slug}"),
        ],
        request,
    )

    tab_items = get_organization_tabs(request, organization_slug=organization_slug)
    context = {
        "base_href": f"/organizations/{organization_slug}",
        "organization": organization,
        "organization_id": organization.id,
        "tab_items": tab_items,
        "breadcrumbs": breadcrumbs,
    }
    return templates.TemplateResponse(request, "organizations/home.html.j2", context)


async def get_organization_or_error(
    organizations_service: OrganizationsService, request: Request, organization_slug: str
) -> Organization:
    try:
        organization = await organizations_service.find_by_slug(organization_slug)
        request.state.path_variables = {"organization_slug": organization.slug}
    except AMTRepositoryError as e:
        raise AMTNotFound from e
    return organization


@router.get("/{organization_slug}/edit")
@permission({AuthorizationResource.ORGANIZATION_INFO_SLUG: [AuthorizationVerb.UPDATE]})
async def get_organization_edit(
    request: Request,
    organizations_service: Annotated[OrganizationsService, Depends(OrganizationsService)],
    organization_slug: str,
    full_resource_path: str,
) -> HTMLResponse:
    organization = await get_organization_or_error(organizations_service, request, organization_slug)

    editable: ResolvedEditable = await get_enriched_resolved_editable(
        context_variables={"organization_id": organization.id},
        full_resource_path=full_resource_path,
        organizations_service=organizations_service,
        edit_mode=EditModes.VIEW,
    )

    editable_context = {"organizations_service": organizations_service}

    # TODO: the converter could be done in the get_enriched_resolved_editable as it knows what editmode we are in
    if editable.converter:
        editable.value = await editable.converter.read(editable.value, **editable_context)

    context = {
        "relative_resource_path": editable.relative_resource_path.replace("/", ".")
        if editable.relative_resource_path
        else "",
        "base_href": f"/organizations/{organization_slug}",
        "resource_object": editable.resource_object,
        "full_resource_path": full_resource_path,
        "editable_object": editable,
    }

    return templates.TemplateResponse(request, "parts/edit_cell.html.j2", context)


@router.get("/{organization_slug}/cancel")
@permission({AuthorizationResource.ORGANIZATION_INFO_SLUG: [AuthorizationVerb.UPDATE]})
async def get_organization_cancel(
    request: Request,
    organization_slug: str,
    full_resource_path: str,
    organizations_service: Annotated[OrganizationsService, Depends(OrganizationsService)],
) -> HTMLResponse:
    organization = await get_organization_or_error(organizations_service, request, organization_slug)

    editable: ResolvedEditable = await get_enriched_resolved_editable(
        context_variables={"organization_id": organization.id},
        full_resource_path=full_resource_path,
        organizations_service=organizations_service,
        edit_mode=EditModes.VIEW,
    )

    editable_context = {"organizations_service": organizations_service}

    if editable.converter:
        editable.value = await editable.converter.view(editable.value, **editable_context)

    context = {
        "relative_resource_path": editable.relative_resource_path.replace("/", ".")
        if editable.relative_resource_path
        else "",
        "base_href": f"/organizations/{organization_slug}",
        "resource_object": None,  # TODO: this should become an optional parameter in the Jinja template
        "full_resource_path": full_resource_path,
        "editable_object": editable,
    }

    return templates.TemplateResponse(request, "parts/view_cell.html.j2", context)


@router.put("/{organization_slug}/update")
@permission({AuthorizationResource.ORGANIZATION_INFO_SLUG: [AuthorizationVerb.UPDATE]})
async def get_organization_update(
    request: Request,
    organizations_service: Annotated[OrganizationsService, Depends(OrganizationsService)],
    organization_slug: str,
    full_resource_path: str,
) -> HTMLResponse:
    organization = await get_organization_or_error(organizations_service, request, organization_slug)
    new_values = await request.json()

    user_id = get_user_id_or_error(request)

    context_variables: dict[str, str | int] = {"organization_id": organization.id}

    editable: ResolvedEditable = await get_enriched_resolved_editable(
        context_variables=context_variables,
        full_resource_path=full_resource_path,
        organizations_service=organizations_service,
        edit_mode=EditModes.SAVE,
    )

    editable_context = {
        "user_id": user_id,
        "new_values": new_values,
        "organizations_service": organizations_service,
    }

    editable = await save_editable(
        editable,
        editable_context=editable_context,
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
        "base_href": f"/organizations/{organization_slug}",
        "resource_object": None,
        "full_resource_path": full_resource_path,
        "editable_object": editable,
    }

    # TODO: add a 'next action' to editable for f.e. redirect options, THIS IS A HACK
    if full_resource_path == Editables.ORGANIZATION_SLUG.full_resource_path.format_map(SafeDict(context_variables)):
        return templates.Redirect(request, f"/organizations/{editable.value}")
    else:
        return templates.TemplateResponse(request, "parts/view_cell.html.j2", context)


@permission({AuthorizationResource.ORGANIZATION_INFO_SLUG: [AuthorizationVerb.LIST]})
@router.get("/{organization_slug}/algorithms")
async def show_algorithms(
    request: Request,
    algorithms_service: Annotated[AlgorithmsService, Depends(AlgorithmsService)],
    organizations_service: Annotated[OrganizationsService, Depends(OrganizationsService)],
    users_service: Annotated[UsersService, Depends(UsersService)],
    organization_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, ge=1),  # todo: fix infinite scroll
    search: str = Query(""),
    display_type: str = Query(""),
) -> HTMLResponse:
    organization = await get_organization_or_error(organizations_service, request, organization_slug)
    filters, drop_filters, localized_filters, sort_by = await get_filters_and_sort_by(request, users_service)

    filters["organization-id"] = str(organization.id)
    algorithms, amount_algorithm_systems = await get_algorithms(
        algorithms_service, display_type, filters, limit, request, search, skip, sort_by
    )
    next = skip + limit

    tab_items = get_organization_tabs(request, organization_slug=organization_slug)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ORGANIZATIONS_ROOT,
            BaseNavigationItem(custom_display_text=organization.name, url="/organizations/{organization_slug}"),
            Navigation.ORGANIZATIONS_ALGORITHMS,
        ],
        request,
    )

    context: dict[str, Any] = {
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
        "sub_menu_items": {},
        "algorithms": algorithms,
        "amount_algorithm_systems": amount_algorithm_systems,
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
        "base_href": f"/organizations/{organization_slug}/algorithms",
        "organization_id": organization.id,
    }

    if request.state.htmx and drop_filters:
        return templates.TemplateResponse(request, "parts/algorithm_search.html.j2", context)
    elif request.state.htmx:
        return templates.TemplateResponse(request, "parts/filter_list.html.j2", context)
    else:
        return templates.TemplateResponse(request, "organizations/algorithms.html.j2", context)


@router.delete("/{organization_slug}/members/{user_id}")
@permission({AuthorizationResource.ORGANIZATION_INFO_SLUG: [AuthorizationVerb.UPDATE]})
async def remove_member(
    request: Request,
    organization_slug: str,
    user_id: UUID,
    organizations_service: Annotated[OrganizationsService, Depends(OrganizationsService)],
    users_repository: Annotated[UsersRepository, Depends(UsersRepository)],
) -> HTMLResponse:
    # TODO (Robbert): add authorization and check if user and organization exist?
    organization = await get_organization_or_error(organizations_service, request, organization_slug)
    user: User | None = await users_repository.find_by_id(user_id)
    if user:
        await organizations_service.remove_user(organization, user)
        return templates.Redirect(request, f"/organizations/{organization_slug}/members")
    raise AMTAuthorizationError


@router.get("/{organization_slug}/members/form")
@permission({AuthorizationResource.ORGANIZATION_INFO_SLUG: [AuthorizationVerb.UPDATE]})
async def get_members_form(
    request: Request,
    organization_slug: str,
) -> HTMLResponse:
    form = get_organization_form(id="organization", translations=get_current_translation(request), user=None)
    context: dict[str, Any] = {"form": form, "slug": organization_slug}
    return templates.TemplateResponse(request, "organizations/parts/add_members_modal.html.j2", context)


@router.put("/{organization_slug}/members", response_class=HTMLResponse)
@permission({AuthorizationResource.ORGANIZATION_INFO_SLUG: [AuthorizationVerb.UPDATE]})
async def add_new_members(
    request: Request,
    organization_slug: str,
    organizations_service: Annotated[OrganizationsService, Depends(OrganizationsService)],
    organization_users: OrganizationUsers,
) -> HTMLResponse:
    organization = await get_organization_or_error(organizations_service, request, organization_slug)
    await organizations_service.add_users(organization, organization_users.user_ids)
    return templates.Redirect(request, f"/organizations/{organization_slug}/members")


@router.get("/{organization_slug}/members")
@permission({AuthorizationResource.ORGANIZATION_INFO_SLUG: [AuthorizationVerb.LIST]})
async def get_members(
    request: Request,
    organization_slug: str,
    organizations_service: Annotated[OrganizationsService, Depends(OrganizationsService)],
    users_service: Annotated[UsersService, Depends(UsersService)],
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, ge=1),  # todo: fix infinite scroll
    search: str = Query(""),
) -> HTMLResponse:
    organization = await get_organization_or_error(organizations_service, request, organization_slug)
    filters, drop_filters, localized_filters, sort_by = await get_filters_and_sort_by(request, users_service)
    tab_items = get_organization_tabs(request, organization_slug=organization_slug)
    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ORGANIZATIONS_ROOT,
            BaseNavigationItem(custom_display_text=organization.name, url="/organizations/{organization_slug}"),
            Navigation.ORGANIZATIONS_MEMBERS,
        ],
        request,
    )

    filters["organization-id"] = str(organization.id)
    members = await users_service.find_all(search=search, sort=sort_by, filters=filters)

    context: dict[str, Any] = {
        "slug": organization.slug,
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
        "organization_filters": get_localized_organization_filters(request),
    }

    if request.state.htmx:
        if drop_filters:
            context.update({"include_filters": True})
        return templates.TemplateResponse(request, "organizations/parts/members_results.html.j2", context)
    else:
        context.update({"include_filters": True})
        return templates.TemplateResponse(request, "organizations/members.html.j2", context)
