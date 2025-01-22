from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from amt.models.base import Base


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(length=1024))
    description: Mapped[str]
    sort_order: Mapped[float]
    status_id: Mapped[int | None] = mapped_column(default=None)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("user.id"))
    ## TODO: (Christopher) SQLModel does not allow to give the below restraint an name
    ##       which is needed for alembic. This results in changing the migration file
    ##       manually to give the restrain a name.
    algorithm_id: Mapped[int | None] = mapped_column(ForeignKey("algorithm.id"))
    type: Mapped[str | None]
    type_id: Mapped[str | None]
