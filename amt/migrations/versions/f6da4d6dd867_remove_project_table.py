"""remove project table

Revision ID: f6da4d6dd867
Revises: ff46b7ecc348
Create Date: 2024-11-15 11:30:25.352543

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f6da4d6dd867"
down_revision: str | None = "ff46b7ecc348"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("project")

def downgrade() -> None:
    lifecycle_enum = postgresql.ENUM(name='lifecycle', create_type=False)

    op.create_table(
        "project",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("lifecycle", lifecycle_enum, nullable=True),
        sa.Column("last_edited", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("system_card_json", sa.JSON(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_project"),
    )
