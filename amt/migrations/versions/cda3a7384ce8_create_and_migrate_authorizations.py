"""Create and migrate authorizations

Revision ID: cda3a7384ce8
Revises: 40fd30e75959
Create Date: 2025-03-31 11:21:56.310597

"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import table, column
from sqlalchemy.exc import IntegrityError

from amt.core.authorization import AuthorizationType
from amt.models import Authorization

# revision identifiers, used by Alembic.
revision: str = "cda3a7384ce8"
down_revision: str | None = "40fd30e75959"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

rules_table = table('rule',
                    column('id', sa.Integer),
                    column('resource', sa.String)
                    )

user = sa.table('user',
                 sa.column('id', sa.Integer)
                 )

users_and_organizations = sa.table('users_and_organizations',
                                   sa.column('user_id', sa.UUID),
                                   sa.column('organization_id', sa.Integer)
                                   )

organization = sa.table('organization',
                         sa.column('id', sa.Integer)
                         )

algorithm = sa.table('algorithm',
                      sa.column('id', sa.Integer),
                      sa.column('organization_id', sa.Integer)
                      )

authorization = sa.table('authorization',
                          sa.column('id', sa.Integer),
                                   sa.column('user_id', sa.UUID),
                                   sa.column('role_id', sa.Integer),
                                   sa.column('type_id', sa.Integer),
                                   sa.column('type', sa.String),
                                   )


def upgrade_algorithm_typo(connection):
    results = connection.execute(
        sa.select(rules_table)
        .where(rules_table.c.resource.like('%algoritme%'))
    )
    for row in results:
        current_resource = row.resource
        new_resource = current_resource.replace('algoritme', 'algorithm')
        connection.execute(
            rules_table.update()
            .where(rules_table.c.id == row.id)
            .values(resource=new_resource)
        )

def downgrade_algorithm_typo(connection):
    results = connection.execute(
        sa.select(rules_table)
        .where(rules_table.c.resource.like('%algorithm%'))
    )
    for row in results:
        current_resource = row.resource
        old_resource = current_resource.replace('algorithm', 'algoritme')
        connection.execute(
            rules_table.update()
            .where(rules_table.c.id == row.id)
            .values(resource=old_resource)
        )

def upgrade() -> None:
    upgrade_algorithm_typo(op.get_bind())

    with op.batch_alter_table('authorization') as batch_op:
        batch_op.create_unique_constraint(
            'uq_authorization_user_role_type_typeid',
            ['user_id', 'role_id', 'type', 'type_id']
        )

    results = op.get_bind().execute(sa.select(users_and_organizations))
    organization_authorizations = [{"user_id": row.user_id, "type_id": row.organization_id, "type": AuthorizationType.ORGANIZATION, "role_id": 1} for row in results]

    query = sa.select(
        user.c.id.label('user_id'),
        algorithm.c.id.label('algorithm_id')
    ).select_from(
        user.join(
            users_and_organizations,
            user.c.id == users_and_organizations.c.user_id
        ).join(
            organization,
            organization.c.id == users_and_organizations.c.organization_id
        ).join(
            algorithm,
            algorithm.c.organization_id == organization.c.id
        )
    )
    results = op.get_bind().execute(query)
    algorithm_authorizations = [{"user_id": row.user_id, "type_id": row.algorithm_id, "type": AuthorizationType.ALGORITHM, "role_id": 4} for row in results]

    for row in algorithm_authorizations + organization_authorizations:
        select_stmt = sa.select(authorization).where(
            (authorization.c.user_id == row['user_id']) &
            (authorization.c.type_id == row['type_id']) &
            (authorization.c.type == row['type'])
        )

        # Execute and fetch results
        result = op.get_bind().execute(select_stmt).fetchall()
        if not result:
            op.execute(authorization.insert().values(**row))
        else:
            print(f"Skipping existing row: {row}")

    op.drop_table("users_and_organizations")

def downgrade() -> None:
    downgrade_algorithm_typo(op.get_bind())

    with op.batch_alter_table('authorization') as batch_op:
        batch_op.drop_constraint('uq_authorization_user_role_type_typeid')

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

    # copy users and organizations
    results = op.get_bind().execute(sa.select(authorization).where(authorization.c.type == AuthorizationType.ORGANIZATION))
    new_entries = [{"user_id": row.user_id, "organization_id": row.type_id} for row in results]
    for row in new_entries:
        op.execute(users_and_organizations.insert().values(**row))
