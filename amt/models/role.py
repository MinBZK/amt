from sqlalchemy import Set, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amt.models.base import Base
from amt.models.rule import Rule


class Role(Base):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    rules: Mapped[Set["Rule"]] = relationship(back_populates="role")
