"""drop users table

Revision ID: 22298f3aac77
Revises: 7f20f8562007
Create Date: 2024-11-12 09:33:50.853310

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "22298f3aac77"
down_revision: str | None = "6581a03aabec"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.drop_constraint("fk_task_user_id_user", type_="foreignkey")
    op.drop_column("task", "user_id")
    op.drop_table("user")


def downgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("name", sa.VARCHAR(length=255), nullable=False),
        sa.Column("avatar", sa.VARCHAR(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_user"),
    )
    op.add_column("task", sa.Column("user_id", sa.INTEGER(), nullable=True))
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.create_foreign_key("fk_task_user_id_user", "user", ["user_id"], ["id"])
