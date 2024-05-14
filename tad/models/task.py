from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    title: str
    description: str
    sort_order: float
    status_id: int
    user_id: int | None = Field(default=None, foreign_key="user.id")
