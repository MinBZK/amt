"""add_algorithm_publish_permission

Revision ID: c449b0db56ca
Revises: c76fb66f2c4d
Create Date: 2025-12-15 11:30:20.717198

"""

from collections.abc import Sequence

from alembic import op
from amt.core.authorization import AuthorizationResource, AuthorizationVerb

# revision identifiers, used by Alembic.
revision: str = "c449b0db56ca"
down_revision: str | None = "c76fb66f2c4d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        f"""
        INSERT INTO rule (id, resource, verbs, role_id)
        VALUES (19, '{AuthorizationResource.ALGORITHM_PUBLISH}', '["{AuthorizationVerb.CREATE}"]', 4)
        """  # noqa: S608
    )


def downgrade() -> None:
    op.execute(
        f"""
        DELETE FROM rule
        WHERE resource = '{AuthorizationResource.ALGORITHM_PUBLISH}' AND role_id = 4
        """  # noqa: S608
    )
