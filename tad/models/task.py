from sqlmodel import Field as SQLField  # pyright: ignore [reportUnknownVariableType]
from sqlmodel import SQLModel


class Task(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    title: str
    description: str
    sort_order: float
    status_id: int | None = SQLField(default=None, foreign_key="status.id")
    user_id: int | None = SQLField(default=None, foreign_key="user.id")
    # todo(robbert) Tasks probably are grouped (and sub-grouped), so we probably need a reference to a group_id
