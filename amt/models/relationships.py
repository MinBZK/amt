from sqlalchemy import Column, ForeignKey, Table

from amt.models.base import Base

users_and_organizations = Table(
    "users_and_organizations",
    Base.metadata,
    Column("organization_id", ForeignKey("organization.id"), primary_key=True),  # pyright: ignore[reportUnknownArgumentType]
    Column("user_id", ForeignKey("user.id"), primary_key=True),  # pyright: ignore[reportUnknownArgumentType]
)
