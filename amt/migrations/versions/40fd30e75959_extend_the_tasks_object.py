"""Extend the tasks object

Revision ID: 40fd30e75959
Revises: e16bb3d53cd6
Create Date: 2025-01-21 10:42:12.306602

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "40fd30e75959"
down_revision: str | None = "e16bb3d53cd6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("task", sa.Column("type", sa.String(), nullable=True))
    op.add_column("task", sa.Column("type_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("task", "type_id")
    op.drop_column("task", "type")
