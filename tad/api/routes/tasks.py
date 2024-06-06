from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse

from tad.api.routes.deps import templates
from tad.schema.task import MovedTask
from tad.services.tasks import TasksService

router = APIRouter()


@router.patch("/")
async def move_task(
    request: Request, moved_task: MovedTask, tasks_service: Annotated[TasksService, Depends(TasksService)]
) -> HTMLResponse:
    """
    Move a task through an API call.
    :param tasks_service: the task service
    :param request: the request object
    :param moved_task: the move task object
    :return: a HTMLResponse object, in this case the html code of the card that was moved
    """
    try:
        # because htmx form always sends a value and siblings are optional, we use -1 for None and convert it here
        if moved_task.next_sibling_id == -1:
            moved_task.next_sibling_id = None
        if moved_task.previous_sibling_id == -1:
            moved_task.previous_sibling_id = None
        task = tasks_service.move_task(
            moved_task.id,
            moved_task.status_id,
            moved_task.previous_sibling_id,
            moved_task.next_sibling_id,
        )
        # todo(Robbert) add error handling for input error or task error handling
        return templates.TemplateResponse(request=request, name="task.jinja", context={"task": task})
    except Exception:
        return templates.TemplateResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, request=request, name="error.jinja"
        )
