from sqlmodel import Field, SQLModel  # type: ignore


class Status(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    sort_order: float
