from typing import Annotated

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from tad.services.tasks_service import TasksService

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

tasks_service = TasksService()
env = Environment(loader=FileSystemLoader("tad/site/templates"), autoescape=True)


@router.get("/")
async def test():
    return [{"username": "Rick"}, {"username": "Morty"}]


# TODO this is an ugly work-around, we need a JSON object instead
@router.post("/move", response_class=HTMLResponse)
async def move_task(
    taskId: Annotated[int, Form()],
    statusId: Annotated[int, Form()],
    previousSiblingId: int | None = Form(None),
    nextSiblingId: int | None = Form(None),
):
    task = tasks_service.move_task(taskId, statusId, previousSiblingId, nextSiblingId)
    index_template = env.get_template("task.jinja")
    template_data = {"task": task}
    return index_template.render(template_data)
