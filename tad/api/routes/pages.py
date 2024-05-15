from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from tad.services.statuses import StatusesService
from tad.services.tasks import TasksService

tasks_service = TasksService()
statuses_service = StatusesService()
router = APIRouter()
templates = Jinja2Templates(directory="tad/site/templates")


@router.get("/", response_class=HTMLResponse)
async def default_layout(request: Request):
    context = {
        "page_title": "This is the page title",
        "tasks_service": tasks_service,
        "statuses_service": statuses_service,
    }
    return templates.TemplateResponse(request=request, name="default_layout.jinja", context=context)
