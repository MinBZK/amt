from sqlalchemy import ARRAY, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amt.models.base import Base
from amt.models.role import Role


class Rule(Base):
    __tablename__ = "rule"

    id: Mapped[int] = mapped_column(primary_key=True)
    resources: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    verbs: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"), nullable=False)
    role: Mapped[Role] = relationship(back_populates="rules")
