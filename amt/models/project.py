from typing import TypeVar

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from amt.models.base import Base

T = TypeVar("T", bound="Project")


class Project(Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))  # TODO: (Christopher) how to set min_length?
    model_card: Mapped[str | None] = mapped_column(default=None)
