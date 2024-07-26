from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from amt.api.deps import templates
from amt.enums.status import Status
from amt.services.tasks import TasksService

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def default_layout(
    request: Request,
    tasks_service: Annotated[TasksService, Depends(TasksService)],
) -> HTMLResponse:
    context = {"page_title": "This is the page title", "tasks_service": tasks_service, "statuses": Status}
    return templates.TemplateResponse(request, "pages/index.html.j2", context)
