"""Add system_card_column

Revision ID: 7f20f8562007
Revises: 1019b72fe63a
Create Date: 2024-10-12 14:28:32.153283

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7f20f8562007"
down_revision: str | None = "1019b72fe63a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("project", schema=None) as batch_op:
        batch_op.add_column(sa.Column("system_card_json", sa.JSON(), nullable=True))
        batch_op.drop_column("model_card")


def downgrade() -> None:
    with op.batch_alter_table("project", schema=None) as batch_op:
        batch_op.add_column(sa.Column("model_card", sa.String(), nullable=True))
        batch_op.drop_column("system_card_json")
