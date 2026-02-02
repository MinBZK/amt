from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amt.api.publication_statuses import PublicationStatuses
from amt.models.base import Base


class Publication(Base):
    __tablename__ = "publication"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_code: Mapped[str] = mapped_column(String(255))
    publication_status: Mapped[PublicationStatuses | None] = mapped_column(
        ENUM(PublicationStatuses, name="publication_status"), nullable=True
    )
    publication_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(server_default=None, nullable=True)
    lars: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    algorithm_id: Mapped[int] = mapped_column(ForeignKey("algorithm.id"), nullable=False, unique=True)
    algorithm: Mapped["Algorithm"] = relationship(back_populates="publication", lazy="selectin", uselist=False)  # noqa: F821  # pyright: ignore [reportUndefinedVariable]
