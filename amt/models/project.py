from datetime import datetime
from typing import TypeVar

from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from amt.api.lifecycles import Lifecycles
from amt.models.base import Base

T = TypeVar("T", bound="Project")


class Project(Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    lifecycle: Mapped[Lifecycles | None] = mapped_column(ENUM(Lifecycles), nullable=True)
    model_card: Mapped[str | None] = mapped_column(default=None)
    last_edited: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
