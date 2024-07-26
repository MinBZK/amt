import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from amt.api.deps import templates
from amt.core.exceptions import NotFound
from amt.enums.status import Status
from amt.services.projects import ProjectsService
from amt.services.tasks import TasksService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{project_id}")
async def get_root(
    request: Request,
    project_id: int,
    projects_service: Annotated[ProjectsService, Depends(ProjectsService)],
    tasks_service: Annotated[TasksService, Depends(TasksService)],
) -> HTMLResponse:
    project = projects_service.get(project_id)

    context = {
        "tasks_service": tasks_service,
        "statuses": Status,
        "project": project,
    }

    if not project:
        raise NotFound()

    return templates.TemplateResponse(request, "pages/index.html.j2", context)
