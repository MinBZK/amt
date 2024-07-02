import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from tad.api.deps import templates
from tad.schema.project import ProjectNew
from tad.services.instruments import InstrumentsService
from tad.services.projects import ProjectsService

router = APIRouter()
logger = logging.getLogger(__name__)


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
