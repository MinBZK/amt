from pydantic import BaseModel, ValidationInfo, field_validator
from pydantic import Field as PydanticField
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel


class Task(SQLModel, table=True):
    id: int = SQLField(default=None, primary_key=True)
    title: str
    description: str
    sort_order: float
    status_id: int | None = SQLField(default=None, foreign_key="status.id")
    user_id: int | None = SQLField(default=None, foreign_key="user.id")
    # todo(robbert) Tasks probably are grouped (and sub-grouped), so we probably need a reference to a group_id


class MoveTask(BaseModel):
    # todo(robbert) values from htmx json are all strings, using type int does not work for
    #  sibling variables (they are optional)
    id: str = PydanticField(None, alias="taskId", strict=False)
    status_id: str = PydanticField(None, alias="statusId", strict=False)
    previous_sibling_id: str | None = PydanticField(None, alias="previousSiblingId", strict=False)
    next_sibling_id: str | None = PydanticField(None, alias="nextSiblingId", strict=False)

    @field_validator("id", "status_id", "previous_sibling_id", "next_sibling_id")
    @classmethod
    def check_is_int(cls, value: str, info: ValidationInfo) -> str:
        if value is not None and isinstance(value, str) and value.isdigit():
            assert value.isdigit(), f"{info.field_name} must be an integer"  # noqa: S101
        return value
