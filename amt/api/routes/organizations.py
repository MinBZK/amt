from collections.abc import Sequence
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic_core._pydantic_core import ValidationError  # pyright: ignore

from amt.api.deps import templates
from amt.api.forms.organization import get_organization_form
from amt.api.navigation import (
    BaseNavigationItem,
    Navigation,
    NavigationItem,
    resolve_base_navigation_items,
    resolve_navigation_items,
)
from amt.api.organization_filter_options import get_localized_organization_filters
from amt.api.routes.algorithm import UpdateFieldModel, set_path
from amt.api.routes.shared import get_filters_and_sort_by
from amt.core.authorization import get_user
from amt.core.exceptions import AMTNotFound, AMTRepositoryError
from amt.core.internationalization import get_current_translation
from amt.models import Organization
from amt.repositories.organizations import OrganizationsRepository
from amt.repositories.users import UsersRepository
from amt.schema.organization import OrganizationBase, OrganizationNew, OrganizationSlug
from amt.services.organizations import OrganizationsService

router = APIRouter()


def get_organization_tabs(request: Request, organization_slug: str) -> list[NavigationItem]:
    request.state.path_variables = {"organization_slug": organization_slug}

    return resolve_navigation_items(
        [Navigation.ORGANIZATIONS_INFO, Navigation.ORGANIZATIONS_ALGORITHMS, Navigation.ORGANIZATIONS_PEOPLE],
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
) -> HTMLResponse:
    breadcrumbs = resolve_base_navigation_items([Navigation.ORGANIZATIONS_ROOT, Navigation.ORGANIZATIONS_NEW], request)

    form = get_organization_form(id="organization", translations=get_current_translation(request))

    context: dict[str, Any] = {"form": form, "breadcrumbs": breadcrumbs}

    return templates.TemplateResponse(request, "organizations/new.html.j2", context)


@router.get("/")
async def root(
    request: Request,
    organizations_repository: Annotated[OrganizationsRepository, Depends(OrganizationsRepository)],
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, ge=1),  # todo: fix infinite scroll
    search: str = Query(""),
) -> HTMLResponse:
    filters, drop_filters, localized_filters, sort_by = get_filters_and_sort_by(request)

    user = get_user(request)

    breadcrumbs = resolve_base_navigation_items(
        [Navigation.ORGANIZATIONS_ROOT, Navigation.ORGANIZATIONS_OVERVIEW], request
    )
    organizations: Sequence[Organization] = await organizations_repository.find_by(
        search=search, sort=sort_by, filters=filters, user_id=user["sub"] if user else None
    )

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
        "organization_filters": get_localized_organization_filters(request),
    }

    if request.state.htmx:
        if drop_filters:
            context.update({"include_filters": True})
        return templates.TemplateResponse(request, "organizations/parts/overview_results.html.j2", context)
    else:
        context.update({"include_filters": True})
        return templates.TemplateResponse(request, "organizations/index.html.j2", context)


@router.post("/new", response_class=HTMLResponse)
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


@router.get("/{slug}")
async def get_by_slug(
    request: Request,
    slug: str,
    organizations_repository: Annotated[OrganizationsRepository, Depends(OrganizationsRepository)],
) -> HTMLResponse:
    try:
        organization = await organizations_repository.find_by_slug(slug)
        request.state.path_variables = {"organization_slug": organization.slug}
        breadcrumbs = resolve_base_navigation_items(
            [
                Navigation.ORGANIZATIONS_ROOT,
                BaseNavigationItem(custom_display_text=organization.name, url="/organizations/{organization_slug}"),
            ],
            request,
        )

        tab_items = get_organization_tabs(request, organization_slug=slug)
        context = {
            "base_href": f"/organizations/{ slug }",
            "organization": organization,
            "tab_items": tab_items,
            "breadcrumbs": breadcrumbs,
        }
        return templates.TemplateResponse(request, "organizations/home.html.j2", context)
    except AMTRepositoryError as e:
        raise AMTNotFound from e


@router.get("/{slug}/edit/{path:path}")
async def get_organization_edit(
    request: Request,
    organizations_repository: Annotated[OrganizationsRepository, Depends(OrganizationsRepository)],
    path: str,
    slug: str,
    edit_type: str,
) -> HTMLResponse:
    context: dict[str, Any] = {"base_href": f"/organizations/{ slug }"}
    organization = await organizations_repository.find_by_slug(slug)
    context.update({"path": path.replace("/", "."), "edit_type": edit_type, "object": organization})
    return templates.TemplateResponse(request, "parts/edit_cell.html.j2", context)


@router.get("/{slug}/cancel/{path:path}")
async def get_organization_cancel(
    organizations_repository: Annotated[OrganizationsRepository, Depends(OrganizationsRepository)],
    request: Request,
    path: str,
    edit_type: str,
    slug: str,
) -> HTMLResponse:
    context: dict[str, Any] = {
        "base_href": f"/organizations/{ slug }",
        "path": path.replace("/", "."),
        "edit_type": edit_type,
    }
    organization = await organizations_repository.find_by_slug(slug)
    context.update({"object": organization})
    return templates.TemplateResponse(request, "parts/view_cell.html.j2", context)


@router.put("/{slug}/update/{path:path}")
async def get_organization_update(
    request: Request,
    organizations_repository: Annotated[OrganizationsRepository, Depends(OrganizationsRepository)],
    update_data: UpdateFieldModel,
    path: str,
    edit_type: str,
    slug: str,
) -> HTMLResponse:
    context: dict[str, Any] = {
        "base_href": f"/organizations/{ slug }",
        "path": path.replace("/", "."),
        "edit_type": edit_type,
    }
    organization = await organizations_repository.find_by_slug(slug)
    context.update({"object": organization})

    redirect_to: str | None = None
    # TODO (Robbert) it would be nice to check this on the object.field type (instead of strings)
    if path == "slug":
        try:
            organization_new1: OrganizationSlug = OrganizationSlug(slug=update_data.value)
            OrganizationSlug.model_validate(organization_new1)
            redirect_to = organization_new1.slug
        except ValidationError as e:
            raise RequestValidationError(e.errors()) from e
    elif path == "name":
        try:
            organization_new: OrganizationBase = OrganizationBase(name=update_data.value)
            OrganizationBase.model_validate(organization_new)
        except ValidationError as e:
            raise RequestValidationError(e.errors()) from e

    set_path(organization, path, update_data.value)

    await organizations_repository.save(organization)

    if redirect_to:
        return templates.Redirect(request, f"/organizations/{redirect_to}")
    else:
        return templates.TemplateResponse(request, "parts/view_cell.html.j2", context)


@router.get("/{slug}/algorithms")
async def get_algorithms(
    request: Request,
) -> HTMLResponse:
    return templates.TemplateResponse(request, "pages/under_construction.html.j2", {})


@router.get("/{slug}/people")
async def get_people(
    request: Request,
) -> HTMLResponse:
    return templates.TemplateResponse(request, "pages/under_construction.html.j2", {})
