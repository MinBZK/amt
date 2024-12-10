from sqlalchemy import ARRAY, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amt.models.base import Base


class Rule(Base):
    __tablename__ = "rule"

    id: Mapped[int] = mapped_column(primary_key=True)
    resource: Mapped[str] = mapped_column(String, nullable=False)
    verbs: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"))
    role: Mapped["Role"] = relationship(back_populates="rule")  # pyright: ignore[reportUnknownVariableType, reportUndefinedVariable] #noqa
