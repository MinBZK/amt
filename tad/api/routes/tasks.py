from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from tad.services.tasks import TasksService

router = APIRouter()

tasks_service = TasksService()
templates = Jinja2Templates(directory="tad/site/templates")


@router.get("/")
async def test():
    return [{"username": "Rick"}, {"username": "Morty"}]


@router.post("/move", response_class=HTMLResponse)
async def move_task(request: Request):
    json = await request.json()
    task = tasks_service.move_task(
        int(json["taskId"]), int(json["statusId"]), json["previousSiblingId"], json["nextSiblingId"]
    )
    return templates.TemplateResponse(request=request, name="task.jinja", context={"task": task})
