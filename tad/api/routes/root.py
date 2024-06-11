import random
from typing import Annotated

import yaml
from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from tad.api.routes.deps import templates
from tad.core.config import settings
from tad.services.statuses import StatusesService
from tad.services.tasks import TasksService

router = APIRouter()


@router.get("/")
async def base() -> RedirectResponse:
    return RedirectResponse("/pages/")


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(settings.STATIC_DIR + "/favicon.ico")


@router.post("/form", response_class=HTMLResponse)
@router.get("/form", response_class=HTMLResponse)
async def form_layout(
    request: Request,
):
    with open("sources/iama.yaml") as f:
        questionnaire = yaml.safe_load(f)

    random_number = random.randint(0, len(questionnaire["tasks"]) - 1)  # noqa
    question_types = ["open", "choice", "multiple"]

    context = {
        "page_title": "This is the page title",
        "question_type": question_types[random.randint(0, len(question_types) - 1)],  # noqa
        "question": questionnaire["tasks"][random_number]["question"],
        "metadata": questionnaire["tasks"][random_number],
    }
    return templates.TemplateResponse(request=request, name="form_poc.jinja", context=context)


@router.get("/statuses", response_class=HTMLResponse)
async def columns_layout(
    request: Request,
    status_service: Annotated[StatusesService, Depends(StatusesService)],
    tasks_service: Annotated[TasksService, Depends(TasksService)],
):
    context = {
        "page_title": "This is the page title",
        "tasks_service": tasks_service,
        "statuses_service": status_service,
    }
    return templates.TemplateResponse(request=request, name="task_columns.jinja", context=context)
