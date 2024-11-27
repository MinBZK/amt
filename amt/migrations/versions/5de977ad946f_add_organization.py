"""Add organization

Revision ID: 5de977ad946f
Revises: 69243fd24222
Create Date: 2024-11-19 14:26:41.815333

"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import text
from alembic import op
from sqlalchemy.orm.session import Session

from amt.models import User

# revision identifiers, used by Alembic.
revision: str = "5de977ad946f"
down_revision: str | None = "f6da4d6dd867"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    organization = op.create_table(
        "organization",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("modified_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["user.id"], name=op.f("fk_organization_created_by_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization")),
        sa.UniqueConstraint("slug", name=op.f("uq_organization_slug")),
    )

    users_and_organizations = op.create_table(
        "users_and_organizations",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_users_and_organizations_organization_id_organization"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_users_and_organizations_user_id_user")),
        sa.PrimaryKeyConstraint("organization_id", "user_id", name=op.f("pk_users_and_organizations")),
    )
    op.add_column("algorithm", sa.Column("organization_id", sa.Integer(), nullable=True))

    with op.batch_alter_table("algorithm", schema=None) as batch_op:
        batch_op.create_foreign_key(None, "organization", ["organization_id"], ["id"])

    op.add_column("user", sa.Column("email_hash", sa.String(), nullable=True))
    op.add_column("user", sa.Column("name_encoded", sa.String(), nullable=True))
    op.add_column("user", sa.Column("email", sa.String(), nullable=True))

    session = Session(bind=op.get_bind())

    first_user = session.query(User).first()
    if not first_user:
        first_user = User(id=UUID("1738b1e151dc46219556a5662b26517c"), name="AMT Demo User", email="amt@amt.nl", email_hash="hash123", name_encoded="amt+demo+user")
        session.add(first_user)
        session.commit()
        session.refresh(first_user)

    # add demo organization
    op.bulk_insert(organization,[{"name": "Demo AMT", "slug": "demo-amt", "created_by_id": first_user.id}])

    # add all current users to the demo organization
    op.bulk_insert(
        users_and_organizations,
        [{"organization_id": 1, "user_id": user.id} for user in session.query(User).all()]
    )

    # add all current algorithms to the demo organization
    op.execute("UPDATE algorithm SET organization_id = 1")

    # make organization_id required for all algorithms
    with op.batch_alter_table("algorithm", schema=None) as batch_op:
        batch_op.alter_column("organization_id", nullable=False)


def downgrade() -> None:
    op.drop_column("user", "email")
    op.drop_column("user", "name_encoded")
    op.drop_column("user", "email_hash")

    with op.batch_alter_table("algorithm", schema=None) as batch_op:
        batch_op.drop_constraint("fk_algorithm_organization_id_organization", type_="foreignkey")

    op.drop_column("algorithm", "organization_id")
    op.drop_table("users_and_organizations")
    op.drop_table("organization")
