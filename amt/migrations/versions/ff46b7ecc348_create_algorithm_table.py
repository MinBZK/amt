"""create algorithm table

Revision ID: ff46b7ecc348
Revises: 69243fd24222
Create Date: 2024-11-13 14:47:53.834255

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql, sqlite

# revision identifiers, used by Alembic.
revision: str = "ff46b7ecc348"
down_revision: str | None = "69243fd24222"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

lifecycle_values = [
    'ORGANIZATIONAL_RESPONSIBILITIES',
    'PROBLEM_ANALYSIS',
    'DESIGN',
    'DATA_EXPLORATION_AND_PREPARATION',
    'DEVELOPMENT',
    'VERIFICATION_AND_VALIDATION',
    'IMPLEMENTATION',
    'MONITORING_AND_MANAGEMENT',
    'PHASING_OUT'
]


def upgrade() -> None:

    # get enum type
    lifecycle_enum = postgresql.ENUM(name='lifecycle', create_type=False)

    op.create_table(
        "algorithm",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("lifecycle", lifecycle_enum, nullable=True),
        sa.Column("system_card_json", sa.JSON(), nullable=False),
        sa.Column("last_edited", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_algorithm")),
    )


    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.add_column(sa.Column("algorithm_id", sa.Integer(), nullable=True))
        batch_op.drop_constraint("fk_task_project_id_project", type_="foreignkey")
        batch_op.create_foreign_key(op.f("fk_task_algorithm_id_algorithm"), "algorithm", ["algorithm_id"], ["id"])
        batch_op.drop_column("project_id")

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO algorithm (id, name, lifecycle, system_card_json, last_edited, deleted_at)
            SELECT id, name, lifecycle, system_card_json, last_edited, deleted_at
            FROM project
            """
        )
    )


def downgrade() -> None:
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.add_column(sa.Column("project_id", sa.INTEGER(), nullable=True))
        batch_op.drop_constraint(op.f("fk_task_algorithm_id_algorithm"), type_="foreignkey")
        batch_op.create_foreign_key("fk_task_project_id_project", "project", ["project_id"], ["id"])
        batch_op.drop_column("algorithm_id")

    op.drop_table("algorithm")
