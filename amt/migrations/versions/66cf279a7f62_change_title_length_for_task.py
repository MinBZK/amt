"""change title length for task

Revision ID: 66cf279a7f62
Revises: 9ce2341f2922
Create Date: 2024-08-13 15:33:28.001811

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "66cf279a7f62"
down_revision: str | None = "9ce2341f2922"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.alter_column(
            "title", existing_type=sa.VARCHAR(length=255), type_=sa.String(length=1024), existing_nullable=False
        )


def downgrade() -> None:
    op.execute("UPDATE task SET title=SUBSTRING(title,1,255)")

    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.alter_column(
            "title", existing_type=sa.String(length=1024), type_=sa.VARCHAR(length=255), existing_nullable=False
        )
