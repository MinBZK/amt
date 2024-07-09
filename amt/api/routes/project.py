import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from amt.api.deps import templates
from amt.services.projects import ProjectsService
from amt.services.statuses import StatusesService
from amt.services.tasks import TasksService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{project_id}")
async def get_root(
    request: Request,
    project_id: int,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
    status_service: Annotated[StatusesService, Depends(StatusesService)],
    tasks_service: Annotated[TasksService, Depends(TasksService)],
) -> HTMLResponse:
    project = projects_service.get(project_id)

    context = {
        "tasks_service": tasks_service,
        "statuses_service": status_service,
        "project": project,
    }

    if not project:
        return templates.TemplateResponse(request, "pages/404.html.j2")

    return templates.TemplateResponse(request, "pages/index.html.j2", context)
