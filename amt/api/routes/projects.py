import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse

from amt.api.ai_act_profile import get_ai_act_profile_selector
from amt.api.deps import templates
from amt.api.navigation import Navigation, resolve_base_navigation_items, resolve_sub_menu
from amt.schema.project import ProjectNew
from amt.services.instruments import InstrumentsService
from amt.services.projects import ProjectsService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_root(
    request: Request,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    search: str = Query(""),
) -> HTMLResponse:
    projects = projects_service.paginate(skip=skip, limit=limit, search=search)
    next = skip + limit

    sub_menu_items = resolve_sub_menu([Navigation.PROJECTS_OVERVIEW], request)  # pyright: ignore [reportUnusedVariable] # noqa
    breadcrumbs = resolve_base_navigation_items([Navigation.PROJECTS_ROOT, Navigation.PROJECTS_OVERVIEW], request)

    context: dict[str, Any] = {
        "breadcrumbs": breadcrumbs,
        "sub_menu_items": {},  # sub_menu_items disabled for now
        "projects": projects,
        "next": next,
        "limit": limit,
        "search": search,
    }

    if request.state.htmx:
        return templates.TemplateResponse(
            request, "projects/_list.html.j2", {"projects": projects, "next": next, "search": search, "limit": limit}
        )

    return templates.TemplateResponse(request, "projects/index.html.j2", context)


@router.get("/new")
async def get_new(
    request: Request,
    instrument_service: Annotated[InstrumentsService, Depends(InstrumentsService)],
) -> HTMLResponse:
    sub_menu_items = resolve_sub_menu([Navigation.PROJECTS_OVERVIEW], request)  # pyright: ignore [reportUnusedVariable] # noqa
    breadcrumbs = resolve_base_navigation_items([Navigation.PROJECTS_ROOT, Navigation.PROJECT_NEW], request)

    ai_act_profile = get_ai_act_profile_selector(request)

    context: dict[str, Any] = {
        "instruments": instrument_service.fetch_instruments(),
        "ai_act_profile": ai_act_profile,
        "breadcrumbs": breadcrumbs,
        "sub_menu_items": {},  # sub_menu_items disabled for now,
    }

    response = templates.TemplateResponse(request, "projects/new.html.j2", context)
    return response


@router.post("/new", response_class=HTMLResponse)
async def post_new(
    request: Request,
    project_new: ProjectNew,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
) -> HTMLResponse:
    project = projects_service.create(project_new)
    response = templates.Redirect(request, f"/project/{project.id}/tasks")
    return response
