from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from amt.models.base import Base


class Rule(Base):
    __tablename__ = "rule"

    id: Mapped[int] = mapped_column(primary_key=True)
    resource: Mapped[str] = mapped_column(String, nullable=False)
    verbs: Mapped[list[str]] = mapped_column(JSON, default=list)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"))
