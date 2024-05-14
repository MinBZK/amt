from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from tad.services.tasks_service import TasksService

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

tasks_service = TasksService()
templates = Jinja2Templates(directory="tad/site/templates")


@router.get("/")
async def test():
    return [{"username": "Rick"}, {"username": "Morty"}]


@router.post("/move", response_class=HTMLResponse)
async def move_task(request: Request):
    json = await request.json()
    print(json)
    task = tasks_service.move_task(
        int(json["taskId"]), int(json["statusId"]), json["previousSiblingId"], json["nextSiblingId"]
    )
    return templates.TemplateResponse(request=request, name="task.jinja", context={"task": task})


# TODO this is an ugly work-around, we need a JSON object instead
@router.post("/move-form", response_class=HTMLResponse)
async def move_task_form(
    request: Request,
    taskId: Annotated[int, Form()],
    statusId: Annotated[int, Form()],
    previousSiblingId: int | None = Form(None),
    nextSiblingId: int | None = Form(None),
):
    task = tasks_service.move_task(taskId, statusId, previousSiblingId, nextSiblingId)
    return templates.TemplateResponse(request=request, name="task.jinja", context={"task": task})
