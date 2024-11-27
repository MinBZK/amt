from uuid import UUID

from sqlalchemy import UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amt.models import Organization
from amt.models.base import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(default=None)
    email_hash: Mapped[str] = mapped_column(default=None)
    name_encoded: Mapped[str] = mapped_column(default=None)
    email: Mapped[str] = mapped_column(default=None)
    organizations: Mapped[list["Organization"]] = relationship(
        "Organization", secondary="users_and_organizations", back_populates="users", lazy="selectin"
    )
    organizations_created: Mapped[list["Organization"]] = relationship(back_populates="created_by", lazy="selectin")
