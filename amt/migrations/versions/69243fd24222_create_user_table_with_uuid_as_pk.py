"""create user table with uuid as pk

Revision ID: 69243fd24222
Revises: 22298f3aac77
Create Date: 2024-11-12 09:49:53.558089

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "69243fd24222"
down_revision: str | None = "22298f3aac77"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user")),
    )
    op.add_column("task", sa.Column("user_id", sa.UUID(), nullable=True))
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.create_foreign_key(op.f("fk_task_user_id_user"), "user", ["user_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.drop_constraint(op.f("fk_task_user_id_user"), type_="foreignkey")
    op.drop_column("task", "user_id")
    op.drop_table("user")
