from pydantic import BaseModel
from pydantic import Field as PydanticField


class MovedTask(BaseModel):
    id: int = PydanticField(None, alias="taskId", strict=False)
    status_id: int = PydanticField(None, alias="statusId", strict=False)
    previous_sibling_id: int | None = PydanticField(None, alias="previousSiblingId", strict=False)
    next_sibling_id: int | None = PydanticField(None, alias="nextSiblingId", strict=False)
