import json
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from amt.api.lifecycles import Lifecycles
from amt.models.base import Base
from amt.schema.system_card import SystemCard

T = TypeVar("T", bound="Algorithm")


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:  # noqa: ANN401
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Enum):
            return o.name
        return super().default(o)


class AlgorithmSystemCard(SystemCard):
    def __init__(self, parent: "Algorithm", **data: Any) -> None:  # noqa: ANN401
        super().__init__(**data)
        self._parent = parent

    def __setattr__(self, name: str, value: Any) -> None:  # noqa: ANN401
        super().__setattr__(name, value)
        if name != "_parent" and hasattr(self, "_parent"):
            self._parent.sync_system_card()

    def __eq__(self, other: Any) -> bool:  # noqa: ANN401
        if isinstance(other, AlgorithmSystemCard | SystemCard):
            return self.model_dump(exclude={"_parent"}) == other.model_dump()
        return False

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        exclude_unset = kwargs.pop("exclude_unset", False)
        by_alias = kwargs.pop("by_alias", False)
        exclude_none = kwargs.pop("exclude_none", False)

        dumped = super().model_dump(
            *args, exclude_unset=exclude_unset, by_alias=by_alias, exclude_none=exclude_none, **kwargs
        )

        return json.loads(json.dumps(dumped, cls=CustomJSONEncoder))


class Algorithm(Base):
    __tablename__ = "algorithm"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    lifecycle: Mapped[Lifecycles | None] = mapped_column(ENUM(Lifecycles, name="lifecycle"), nullable=True)
    system_card_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_edited: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(server_default=None, nullable=True)

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        system_card: SystemCard | None = kwargs.pop("system_card", None)
        super().__init__(*args, **kwargs)
        self._system_card: AlgorithmSystemCard | None = None
        if system_card is not None:
            self.system_card = system_card

    @property
    def system_card(self) -> AlgorithmSystemCard:
        if not hasattr(self, "_system_card"):
            self._system_card: AlgorithmSystemCard | None = None

        if self._system_card is None:
            if self.system_card_json:
                self._system_card = AlgorithmSystemCard(self, **self.system_card_json)
            else:
                self._system_card = AlgorithmSystemCard(self)
                self.sync_system_card()
        return self._system_card

    @system_card.setter
    def system_card(self, value: SystemCard | None) -> None:
        if value is None:
            self._system_card = AlgorithmSystemCard(self)
        else:
            self._system_card = AlgorithmSystemCard(self, **value.model_dump(exclude_unset=True, by_alias=True))
        self.sync_system_card()

    def sync_system_card(self) -> None:
        if self._system_card is not None:
            self.system_card_json = self._system_card.model_dump(exclude_unset=True, by_alias=True)


Algorithm.__mapper_args__ = {"exclude_properties": ["_system_card"]}
