from uuid import UUID

from pydantic import BaseModel
from pydantic import Field as PydanticField

from amt.models import Task
from amt.schema.measure_display import DisplayMeasureTask


class MovedTask(BaseModel):
    id: int = PydanticField(alias="taskId", strict=False)
    status_id: int = PydanticField(alias="statusId", strict=False)
    previous_sibling_id: int | None = PydanticField(None, alias="previousSiblingId", strict=False)
    next_sibling_id: int | None = PydanticField(None, alias="nextSiblingId", strict=False)


class DisplayTask(BaseModel):
    id: int | None = None
    title: str | None = None
    description: str | None = None
    sort_order: float | None = None
    status_id: int | None = None
    user_id: UUID | None = None
    algorithm_id: int | None = None
    type: str | None = None
    type_id: str | None = None
    type_object: DisplayMeasureTask | None = None

    @staticmethod
    def create_from_model(task: Task, type_object: DisplayMeasureTask | None = None) -> "DisplayTask":
        display_task = DisplayTask()
        display_task.id = task.id
        display_task.title = task.title
        display_task.description = task.description
        display_task.sort_order = task.sort_order
        display_task.status_id = task.status_id
        display_task.user_id = task.user_id
        display_task.algorithm_id = task.algorithm_id
        display_task.type = task.type
        display_task.type_id = task.type_id
        if type_object is not None:
            display_task.type_object = type_object
            display_task.title = type_object.name
        return display_task
