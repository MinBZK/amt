from datetime import datetime
from typing import Any, TypeVar

from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from amt.api.lifecycles import Lifecycles
from amt.models.base import Base
from amt.schema.system_card import SystemCard

T = TypeVar("T", bound="Project")


class ProjectSystemCard(SystemCard):
    def __init__(self, parent: "Project", **data: Any) -> None:  # noqa: ANN401
        super().__init__(**data)
        self._parent = parent

    def __setattr__(self, name: str, value: Any) -> None:  # noqa: ANN401
        super().__setattr__(name, value)
        if name != "_parent" and hasattr(self, "_parent"):
            self._parent.sync_system_card()

    def __eq__(self, other: Any) -> bool:  # noqa: ANN401
        if isinstance(other, ProjectSystemCard | SystemCard):
            return self.model_dump(exclude={"_parent"}) == other.model_dump()
        return False


class Project(Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    lifecycle: Mapped[Lifecycles | None] = mapped_column(ENUM(Lifecycles), nullable=True)
    system_card_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_edited: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        system_card: SystemCard | None = kwargs.pop("system_card", None)
        super().__init__(*args, **kwargs)
        self._system_card: ProjectSystemCard | None = None
        if system_card is not None:
            self.system_card = system_card

    @property
    def system_card(self) -> ProjectSystemCard:
        if not hasattr(self, "_system_card"):
            self._system_card: ProjectSystemCard | None = None

        if self._system_card is None:
            if self.system_card_json:
                self._system_card = ProjectSystemCard(self, **self.system_card_json)
            else:
                self._system_card = ProjectSystemCard(self)
                self.sync_system_card()
        return self._system_card

    @system_card.setter
    def system_card(self, value: SystemCard | None) -> None:
        if value is None:
            self._system_card = ProjectSystemCard(self)
        else:
            self._system_card = ProjectSystemCard(self, **value.model_dump(exclude_unset=True))
        self.sync_system_card()

    def sync_system_card(self) -> None:
        if self._system_card is not None:
            self.system_card_json = self._system_card.model_dump(exclude_unset=True)


Project.__mapper_args__ = {"exclude_properties": ["_system_card"]}
