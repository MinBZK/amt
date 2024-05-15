from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    title: str
    description: str
    sort_order: float
    status_id: int | None = Field(default=None, foreign_key="status.id")
    user_id: int | None = Field(default=None, foreign_key="user.id")
    # todo(robbert) Tasks probably are grouped (and sub-grouped), so we probably need a reference to a group_id
