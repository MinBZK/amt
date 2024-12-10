from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amt.models.base import Base
from amt.models.relationships import role_and_algorithms, role_and_organizations, users_and_organizations
from amt.models.rule import Rule


class Role(Base):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    rules: Mapped[list["Rule"]] = relationship(back_populates="role")
    users: Mapped[list["User"]] = relationship(  # pyright: ignore[reportUnknownVariableType, reportUndefinedVariable] #noqa
        secondary=users_and_organizations, back_populates="roles", lazy="selectin"
    )
    organizations: Mapped[list["Organization"]] = relationship(  # pyright: ignore[reportUnknownVariableType, reportUndefinedVariable] #noqa
        secondary=role_and_organizations, back_populates="roles", lazy="selectin"
    )
    algorithms: Mapped[list["Algorithm"]] = relationship(  # pyright: ignore[reportUnknownVariableType, reportUndefinedVariable] #noqa
        secondary=role_and_algorithms, back_populates="roles", lazy="selectin"
    )

    # todo: add orgainzation_id later when flexible roles are implemented
