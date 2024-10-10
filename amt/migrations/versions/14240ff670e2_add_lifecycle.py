"""Add lifecycle field to project table

Revision ID: 14240ff670e2
Revises: 66cf279a7f62
Create Date: 2024-10-10 16:26:52.294477

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "14240ff670e2"
down_revision: str | None = "66cf279a7f62"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Define the Lifecycle enum values
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
    # Create the enum type
    lifecycle_enum = postgresql.ENUM(*lifecycle_values, name='lifecycle')
    lifecycle_enum.create(op.get_bind())

    # Add the lifecycle column
    op.add_column('project', sa.Column('lifecycle', lifecycle_enum, nullable=True))


def downgrade() -> None:
    # Remove the lifecycle column
    op.drop_column('project', 'lifecycle')

    # Drop the enum type
    lifecycle_enum = postgresql.ENUM(*lifecycle_values, name='lifecycle')
    lifecycle_enum.drop(op.get_bind())
