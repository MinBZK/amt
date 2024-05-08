from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from tad.models.task import Task

env = Environment(loader=FileSystemLoader("tad/site/templates"), autoescape=True)

router = APIRouter(
    prefix="/pages",
    tags=["pages"],
)


@router.get("/", response_class=HTMLResponse)
async def default_layout():
    index_template = env.get_template("default_layout.jinja")
    task1 = Task(id=1, title="This is title 1", description="This is description 1", status="todo")
    task2 = Task(id=2, title="This is title 2", description="This is description 2", status="todo")
    template_data = {"page_title": "This is the page title", "tasks": [task1, task2]}
    return index_template.render(template_data)
