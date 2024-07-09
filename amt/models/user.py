from sqlmodel import Field, SQLModel  # pyright: ignore [reportUnknownVariableType]


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    avatar: str | None
