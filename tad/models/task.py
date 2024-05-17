from pydantic import BaseModel
from pydantic.fields import Field as PydanticField
from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    title: str
    description: str
    sort_order: float
    status_id: int | None = Field(default=None, foreign_key="status.id")
    user_id: int | None = Field(default=None, foreign_key="user.id")
    # todo(robbert) Tasks probably are grouped (and sub-grouped), so we probably need a reference to a group_id


class MoveTask(BaseModel):
    # todo(robbert) values from htmx json are all strings, using type int does not work for
    #  sibling variables (they are optional)
    id: int = PydanticField(None, alias="taskId", strict=False)
    status_id: int = PydanticField(None, alias="statusId", strict=False)
    previous_sibling_id: str | None = PydanticField(None, alias="previousSiblingId", strict=False)
    next_sibling_id: str | None = PydanticField(None, alias="nextSiblingId", strict=False)
