from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from tad.services.tasks_service import TasksService

env = Environment(loader=FileSystemLoader("tad/site/templates"), autoescape=True)
tasks_service = TasksService()

router = APIRouter(
    prefix="/pages",
    tags=["pages"],
)


@router.get("/", response_class=HTMLResponse)
async def default_layout():
    index_template = env.get_template("default_layout.jinja")
    template_data = {"page_title": "This is the page title", "tasks_service": tasks_service}
    return index_template.render(template_data)
