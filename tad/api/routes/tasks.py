from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from tad.models.task import MoveTask
from tad.services.tasks import TasksService

router = APIRouter()
templates = Jinja2Templates(directory="tad/site/templates")


@router.post("/move", response_class=HTMLResponse)
async def move_task(request: Request, move_task: MoveTask) -> HTMLResponse:
    """
    Move a task through an API call.
    :param request: the request object
    :param move_task: the move task object
    :return: a HTMLResponse object, in this case the html code of the card that was moved
    """
    task = TasksService.move_task(
        move_task.id,
        move_task.status_id,
        convert_to_int_if_is_int(move_task.previous_sibling_id),
        convert_to_int_if_is_int(move_task.next_sibling_id),
    )
    return templates.TemplateResponse(request=request, name="task.jinja", context={"task": task})


def convert_to_int_if_is_int(value: Any) -> int | Any:
    # If the given value is of type integer, convert it to integer, otherwise return the given value
    if isinstance(value, int):
        return int(value)
    return value
