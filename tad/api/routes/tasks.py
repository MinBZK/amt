from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from tad.models.task import MoveTask
from tad.services.tasks import TasksService

router = APIRouter()
templates = Jinja2Templates(directory="tad/site/templates")


@router.post("/move", response_class=HTMLResponse)
async def move_task(
    request: Request, move_task: MoveTask, tasks_service: Annotated[TasksService, Depends(TasksService)]
) -> HTMLResponse:
    """
    Move a task through an API call.
    :param tasks_service: the task service
    :param request: the request object
    :param move_task: the move task object
    :return: a HTMLResponse object, in this case the html code of the card that was moved
    """
    try:
        print("hello I am here", flush=True)
        task = tasks_service.move_task(
            convert_to_int_if_is_int(move_task.id),
            convert_to_int_if_is_int(move_task.status_id),
            convert_to_int_if_is_int(move_task.previous_sibling_id),
            convert_to_int_if_is_int(move_task.next_sibling_id),
        )
        # todo(Robbert) add error handling for input error or task error handling
        return templates.TemplateResponse(request=request, name="task.jinja", context={"task": task})
    except Exception:
        print("All is broken", flush=True)
        return templates.TemplateResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, request=request, name="error.jinja"
        )


def convert_to_int_if_is_int(value: Any) -> int | Any:
    """
    If the given value is of type int, return it as int, otherwise return the input value as is.
    :param value: the value to convert
    :return: the value as int or the original type
    """
    if value is not None and isinstance(value, str) and value.isdigit():
        return int(value)
    return value
