"""rename status fields for translation support

Revision ID: bf86033947fc
Revises: b62dbd9468e4
Create Date: 2024-07-05 08:54:30.114471

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import String
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision: str = "bf86033947fc"
down_revision: str | None = "b62dbd9468e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

status_table = table("status", column("name", String))
status_renames = {"Todo": "todo", "In Progress": "in_progress", "Review": "review", "Done": "done"}


def upgrade() -> None:
    for k, v in status_renames.items():
        op.execute(
            status_table.update()
            .where(status_table.c.name == op.inline_literal(k))
            .values({"name": op.inline_literal(v)})
        )


def downgrade() -> None:
    for k, v in status_renames.items():
        op.execute(
            status_table.update()
            .where(status_table.c.name == op.inline_literal(v))
            .values({"name": op.inline_literal(k)})
        )
