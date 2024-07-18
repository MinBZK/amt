import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse

from amt.api.deps import templates
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
) -> HTMLResponse:
    projects = projects_service.paginate(skip=skip, limit=limit)
    next = skip + limit

    if request.state.htmx:
        return templates.TemplateResponse(request, "projects/_list.html.j2", {"projects": projects, "next": next})

    return templates.TemplateResponse(
        request, "projects/index.html.j2", {"projects": projects, "next": next, "limit": limit}
    )


@router.get("/new")
async def get_new(
    request: Request,
    instrument_service: Annotated[InstrumentsService, Depends(InstrumentsService)],
) -> HTMLResponse:
    instruments = instrument_service.fetch_instruments()

    return templates.TemplateResponse(request, "projects/new.html.j2", {"instruments": instruments})


@router.post("/new", response_class=HTMLResponse)
async def post_new(
    request: Request,
    project_new: ProjectNew,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
) -> HTMLResponse:
    project = projects_service.create(project_new)

    return templates.Redirect(request, f"/project/{project.id}")
