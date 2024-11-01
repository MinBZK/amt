"""add deleted_at to project

Revision ID: 6581a03aabec
Revises: 7f20f8562007
Create Date: 2024-11-01 10:29:58.930558

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = "6581a03aabec"
down_revision: str | None = "7f20f8562007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("project", sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("project", "deleted_at")
