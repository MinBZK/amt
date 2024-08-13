"""add reference to project in task

Revision ID: 2c84c4ad5b68
Revises: c21dd0bc2c85
Create Date: 2024-07-22 15:28:45.628332

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2c84c4ad5b68"
down_revision: str | None = "c21dd0bc2c85"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.add_column(sa.Column("project_id", sa.Integer(), nullable=True))
        # Note that the value None below is due to the automatic naming generation from Base.metadata
        batch_op.create_foreign_key(None, "project", ["project_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("task", schema=None) as batch_op:
        # Drop constraint in batch mode lacks the fields to use automatic naming convention
        batch_op.drop_constraint("fk_task_project_id_project", type_="foreignkey")
        batch_op.drop_column("project_id")
