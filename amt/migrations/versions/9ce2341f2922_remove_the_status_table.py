"""Remove the status table

Revision ID: 9ce2341f2922
Revises: 2c84c4ad5b68
Create Date: 2024-07-26 08:41:52.338277

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9ce2341f2922"
down_revision: str | None = "2c84c4ad5b68"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("task") as batch_op:
        batch_op.drop_constraint(
            "fk_task_status_id_status", type_="foreignkey")

    op.drop_table("status")
    # ### end Alembic commands ###


def downgrade() -> None:
    op.create_table(
        "status",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sort_order", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute("UPDATE task SET status_id = NULL")

    with op.batch_alter_table("task") as batch_op:
        batch_op.create_foreign_key(None, "status", ["status_id"], ["id"])
