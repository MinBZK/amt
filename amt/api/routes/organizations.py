from collections.abc import Sequence
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

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
from amt.api.routes.algorithms import get_algorithms
from amt.api.routes.shared import get_filters_and_sort_by
from amt.core.authorization import AuthorizationResource, AuthorizationType, AuthorizationVerb, get_user
from amt.core.exceptions import AMTAuthorizationError, AMTNotFound, AMTRepositoryError
from amt.core.internationalization import get_current_translation
from amt.models import Authorization, Organization, User
from amt.repositories.organizations import OrganizationsRepository
from amt.schema.organization import OrganizationNew
from amt.services.algorithms import AlgorithmsService
from amt.services.authorization import AuthorizationsService
from amt.services.organizations import OrganizationsService
from amt.services.services_provider import ServicesProvider, get_service_provider
from amt.services.users import UsersService

router = APIRouter()


async def get_users_for_organization(
    authorizations_service: AuthorizationsService, organization: Organization
) -> Sequence[User]:
    filters: dict[str, int | str | list[str | int]] = {
        "type": AuthorizationType.ORGANIZATION,
        "type_id": organization.id,
    }
    members = await authorizations_service.find_all(filters=filters)
    return [user for user, _, _, _ in members]


def get_organization_tabs(request: Request, organization_slug: str) -> list[NavigationItem]:
    request.state.path_variables = {"organization_slug": organization_slug}

    return resolve_navigation_items(
        [Navigation.ORGANIZATIONS_INFO, Navigation.ORGANIZATIONS_ALGORITHMS, Navigation.ORGANIZATIONS_MEMBERS],
        request,
    )


@router.get("/users")
async def get_users(
    request: Request,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> Response:
    organizations_service = await services_provider.get(OrganizationsService)
    authorizations_service = await services_provider.get(AuthorizationsService)
    users_service = await services_provider.get(UsersService)
    query = request.query_params.get("query", None)
    organization_id = request.query_params.get("organization_id", None)
    return_type = request.query_params.get("returnType", "json")
    search_results = []
    organization = None if organization_id is None else await organizations_service.get_by_id(int(organization_id))
    show_no_results = False
    if query and len(query) >= 2:
        search_results: Sequence[User] = await users_service.find_all(search=query, limit=5)  # pyright: ignore[reportDeprecated]
        show_no_results = len(search_results) == 0
    match return_type:
        case "search_select_field":
            organization_id = organization.id if organization else None
            editables: list[ResolvedEditable] = []
            for user in search_results:
                enriched_editable = await create_editable_for_role(
                    request,
                    services_provider,
                    user,
                    AuthorizationType.ORGANIZATION,
                    organization_id,
                    (await authorizations_service.get_role("Organization Member")).id,
                )
                editables.append(enriched_editable)
            context = {"editables": editables, "show_no_results": show_no_results}
            return templates.TemplateResponse(request, "organizations/parts/search_select_field.html.j2", context)
        case _:
            json_results: list[dict[str, str | UUID]] = [
                {"value": str(user.id), "display_value": user.name} for user in search_results
            ]
            return JSONResponse(content=json_results)


@router.get("/new")
async def get_new(
    request: Request,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    breadcrumbs = resolve_base_navigation_items([Navigation.ORGANIZATIONS_ROOT, Navigation.ORGANIZATIONS_NEW], request)
    users_service = await services_provider.get(UsersService)
    # todo (Robbert): make object SessionUser so it can be used as alternative for Database User
    session_user = get_user(request)
    if session_user:
        user = await users_service.find_by_id(session_user["sub"])
        form = await get_organization_form(
            id="organization",
            request=request,
            translations=get_current_translation(request),
            user=user,
            organization=None,
        )
        context: dict[str, Any] = {"form": form, "breadcrumbs": breadcrumbs}
        return templates.TemplateResponse(request, "organizations/new.html.j2", context)
    raise AMTAuthorizationError()


@router.get("/")
@permission({AuthorizationResource.ORGANIZATIONS: [AuthorizationVerb.LIST]})
async def root(
    request: Request,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, ge=1),  # todo: fix infinite scroll
    search: str = Query(""),
) -> HTMLResponse:
    organizations_repository = await services_provider.get_repository(OrganizationsRepository)
    users_service = await services_provider.get(UsersService)
    authorizations_service = await services_provider.get(AuthorizationsService)
    filters, drop_filters, localized_filters, sort_by = await get_filters_and_sort_by(request, users_service)

    user = get_user(request)

    breadcrumbs = resolve_base_navigation_items(
        [Navigation.ORGANIZATIONS_ROOT, Navigation.ORGANIZATIONS_OVERVIEW], request
    )
    filters = {"organization-type": OrganizationFilterOptions.MY_ORGANIZATIONS.value}
    organizations: Sequence[Organization] = await organizations_repository.find_by(
        search=search, sort=sort_by, filters=filters, user_id=user["sub"] if user else None
    )
    # TODO this is probably not the most efficient way to do this..
    #  also, we add an unknown attribute to organizations; this should/could be become a DTO
    for organization in organizations:
        organization.users = await get_users_for_organization(authorizations_service, organization)  # pyright: ignore[reportAttributeAccessIssue]

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
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    current_state_str: str = Header("VALIDATE", alias="X-Current-State"),
) -> HTMLResponse:
    user_id = get_user_id_or_error(request)
    organizations_service = await services_provider.get(OrganizationsService)

    organization = await organizations_service.save(
        name=organization_new.name,
        slug=organization_new.slug,
        created_by_user_id=(user_id),  # pyright: ignore[reportUnknownArgumentType]
    )

    context_variables: dict[str, Any] = {"organization": organization}

    return await update_handler(
        request,
        "authorization",
        f"/organizations/{organization.slug}",
        current_state_str,
        context_variables,
        EditModes.SAVE_NEW,
        services_provider,
    )


@router.get("/{organization_slug}")
@permission({AuthorizationResource.ORGANIZATION_INFO_SLUG: [AuthorizationVerb.READ]})
async def get_by_slug(
    request: Request,
    organization_slug: str,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    organizations_service = await services_provider.get(OrganizationsService)
    authorizations_service = await services_provider.get(AuthorizationsService)
    organization = await get_organization_or_error(organizations_service, request, organization_slug)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ORGANIZATIONS_ROOT,
            BaseNavigationItem(custom_display_text=organization.name, url="/organizations/{organization_slug}"),
        ],
        request,
    )

    organization.users = await get_users_for_organization(authorizations_service, organization)  # pyright: ignore[reportAttributeAccessIssue]

    tab_items = get_organization_tabs(request, organization_slug=organization_slug)
    context = {
        "base_href": f"/organizations/{organization_slug}",
        "organization": organization,
        "organization_id": organization.id,
        "tab_items": tab_items,
        "breadcrumbs": breadcrumbs,
        "editables": get_resolved_editables(context_variables={"organization_id": organization.id}),
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
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    organization_slug: str,
    full_resource_path: str,
) -> HTMLResponse:
    # TODO FIXME: this is too much of a hack! Find a better way
    request.state.authorization_type = AuthorizationType.ORGANIZATION
    organizations_service = await services_provider.get(OrganizationsService)
    organization = await get_organization_or_error(organizations_service, request, organization_slug)
    user_id = get_user_id_or_error(request)
    context_variables: dict[str, Any] = {"organization": organization}
    matched_editable, extracted_context_variables = find_matching_editable(full_resource_path)
    context_variables.update(extracted_context_variables)
    resolved_editable = get_resolved_editable(matched_editable, context_variables, False)
    editable = await enrich_editable(
        resolved_editable, EditModes.EDIT, {"user_id": user_id}, services_provider, request, None
    )

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
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    organizations_service = await services_provider.get(OrganizationsService)
    organization = await get_organization_or_error(organizations_service, request, organization_slug)

    user_id = get_user_id_or_error(request)
    context_variables: dict[str, Any] = {"organization": organization}
    matched_editable, extracted_context_variables = find_matching_editable(full_resource_path)
    context_variables.update(extracted_context_variables)
    resolved_editable = get_resolved_editable(matched_editable, context_variables, False)
    editable = await enrich_editable(
        resolved_editable, EditModes.VIEW, {"user_id": user_id}, services_provider, request, None
    )

    context = {
        # TODO: SET PERMISSION FOR EACH EDITABLE!!
        "has_permission": True,
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
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    organization_slug: str,
    full_resource_path: str,
    current_state_str: str = Header("VALIDATE", alias="X-Current-State"),
) -> HTMLResponse:
    organizations_service = await services_provider.get(OrganizationsService)
    organization = await get_organization_or_error(organizations_service, request, organization_slug)
    context_variables: dict[str, str | int] = {"organization_id": organization.id}

    return await update_handler(
        request,
        full_resource_path,
        f"/organizations/{organization_slug}",
        current_state_str,
        context_variables,
        EditModes.SAVE,
        services_provider,
    )


@permission({AuthorizationResource.ORGANIZATION_ALGORITHM_SLUG: [AuthorizationVerb.LIST]})
@router.get("/{organization_slug}/algorithms")
async def show_algorithms(
    request: Request,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    organization_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, ge=1),  # todo: fix infinite scroll
    search: str = Query(""),
    display_type: str = Query(""),
) -> HTMLResponse:
    organizations_service = await services_provider.get(OrganizationsService)
    algorithms_service = await services_provider.get(AlgorithmsService)
    users_service = await services_provider.get(UsersService)
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
        "permission_path": AuthorizationResource.ORGANIZATION_ALGORITHM.format_map(
            {"organization_id": organization.id}
        ),
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
@permission({AuthorizationResource.ORGANIZATION_MEMBER_SLUG: [AuthorizationVerb.DELETE]})
async def remove_member(
    request: Request,
    organization_slug: str,
    user_id: UUID,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    organizations_service = await services_provider.get(OrganizationsService)
    users_service = await services_provider.get(UsersService)
    authorizations_service = await services_provider.get(AuthorizationsService)
    algorithms_service = await services_provider.get(AlgorithmsService)

    organization = await get_organization_or_error(organizations_service, request, organization_slug)
    user: User | None = await users_service.find_by_id(user_id)
    if user is None:
        raise AMTNotFound()
    authorization = await authorizations_service.find_by_user_and_type(
        user.id, organization.id, AuthorizationType.ORGANIZATION
    )

    editable_context = {
        "organization_id": organization.id,
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
    # When removing a user from an organization,
    #  also check if it is the only maintainer of an algorithm of this organization and fail if true
    algorithms = await algorithms_service.get_by_user_and_organization(user_id, organization.id)

    algorithm_authorizations: Sequence[Authorization] = [
        await authorizations_service.find_by_user_and_type(user_id, algorithm.id, AuthorizationType.ALGORITHM)
        for algorithm in algorithms
    ]
    for algorithm_authorization in algorithm_authorizations:
        algorithm_context = {
            "algorithm_id": algorithm_authorization.type_id,
            "authorization_id": algorithm_authorization.id,
            "new_values": {"role_id": "0"},
        }
        resolved_editable_for_algorithm = get_resolved_editable(Editables.AUTHORIZATION_ROLE, editable_context, False)
        resolved_editable_for_algorithm.resource_object = Authorization(user_id=user.id)

        await EditableEnforcerMustHaveMaintainer().enforce(
            request,
            resolved_editable_for_algorithm,
            algorithm_context,
            EditModes.DELETE,
            services_provider,
        )
    if user:
        await organizations_service.remove_user(organization, user)
        return templates.Redirect(request, f"/organizations/{organization_slug}/members")
    raise AMTAuthorizationError


@router.get("/{organization_slug}/members/form")
@permission({AuthorizationResource.ORGANIZATION_MEMBER_SLUG: [AuthorizationVerb.UPDATE]})
async def get_members_form(
    request: Request,
    organization_slug: str,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    organizations_service = await services_provider.get(OrganizationsService)
    organization = await get_organization_or_error(organizations_service, request, organization_slug)
    form = await get_organization_form(
        id="organization",
        request=request,
        translations=get_current_translation(request),
        user=None,
        organization=organization,
    )
    context: dict[str, Any] = {
        "form": form,
        "base_href": f"/organizations/{organization_slug}",
    }
    return templates.TemplateResponse(request, "organizations/parts/add_members_modal.html.j2", context)


@router.put("/{organization_slug}/members", response_class=HTMLResponse)
@permission({AuthorizationResource.ORGANIZATION_MEMBER_SLUG: [AuthorizationVerb.UPDATE]})
async def add_new_members(
    request: Request,
    organization_slug: str,
    service_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    current_state_str: str = Header("VALIDATE", alias="X-Current-State"),
) -> HTMLResponse:
    organizations_service = await service_provider.get(OrganizationsService)
    organization = await get_organization_or_error(organizations_service, request, organization_slug)
    context_variables: dict[str, Any] = {
        "organization": organization,
    }

    return await update_handler(
        request,
        "authorization",
        f"/organizations/{organization_slug}",
        current_state_str,
        context_variables,
        EditModes.SAVE_NEW,
        service_provider,
    )


@router.get("/{organization_slug}/members")
@permission({AuthorizationResource.ORGANIZATION_MEMBER_SLUG: [AuthorizationVerb.LIST]})
async def get_members(
    request: Request,
    organization_slug: str,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, ge=1),  # todo: fix infinite scroll
    search: str = Query(""),
) -> HTMLResponse:
    request.state.services_provider = services_provider
    organizations_service = await services_provider.get(OrganizationsService)
    authorizations_service = await services_provider.get(AuthorizationsService)
    users_service = await services_provider.get(UsersService)
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

    if "name" not in sort_by:
        sort_by["name"] = "ascending"

    filters: dict[str, int | str | list[str | int]] = {
        "type": AuthorizationType.ORGANIZATION,
        "type_id": organization.id,
    }
    members = await authorizations_service.find_all(search, sort_by, filters, skip, limit)

    context: dict[str, Any] = {
        "base_href": f"/organizations/{organization_slug}",
        "slug": organization.slug,
        "permission_path": AuthorizationResource.ORGANIZATION_MEMBER.format_map({"organization_id": organization.id}),
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
