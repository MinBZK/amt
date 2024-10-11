"""Add last_edited column to projects table

Revision ID: 1019b72fe63a
Revises: 14240ff670e2
Create Date: 2024-10-11 11:56:27.232609

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1019b72fe63a"
down_revision: str | None = "14240ff670e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add last_edited column with default value of current timestamp
    op.add_column('project',
                  sa.Column('last_edited', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))


def downgrade() -> None:
    # Drop the last_edited column
    op.drop_column('project', 'last_edited')
