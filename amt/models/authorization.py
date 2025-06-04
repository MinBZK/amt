from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amt.models.base import Base


class Authorization(Base):
    __tablename__ = "authorization"
    __allow_unmapped__ = True  # Allow unmapped attributes

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(back_populates="authorizations")  # pyright: ignore [reportUndefinedVariable, reportUnknownVariableType] #noqa
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"))
    type: Mapped[str]  # type [Organization or Algorithm] - using str instead of Enum for db compatibility
    type_id: Mapped[int]  # ID of the organization or algorithm
    type_object: Base | None = None
