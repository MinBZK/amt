from uuid import UUID

from sqlalchemy import UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column

from amt.models.base import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), primary_key=True)
    name: Mapped[str]
