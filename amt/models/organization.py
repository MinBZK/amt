from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amt.models.base import Base
from amt.models.relationships import users_and_organizations


class Organization(Base):
    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    modified_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime] = mapped_column(nullable=True)
    users: Mapped[list["User"]] = relationship(  # pyright: ignore[reportUnknownVariableType, reportUndefinedVariable] #noqa
        secondary=users_and_organizations, back_populates="organizations", lazy="selectin"
    )
    algorithms: Mapped[list["Algorithm"]] = relationship(back_populates="organization", lazy="selectin")  # pyright: ignore[reportUnknownVariableType, reportUndefinedVariable] #noqa
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    created_by: Mapped["User"] = relationship(back_populates="organizations_created", lazy="selectin")  # pyright: ignore [reportUndefinedVariable, reportUnknownVariableType] #noqa
