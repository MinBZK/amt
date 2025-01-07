from uuid import UUID

import pytest
from amt.core.authorization import AuthorizationResource, AuthorizationType, AuthorizationVerb
from amt.repositories.authorizations import AuthorizationRepository
from tests.constants import (
    default_algorithm,
    default_auth_user,
    default_authorization,
    default_role,
    default_rule,
    default_user,
)
from tests.database_test_utils import DatabaseTestUtils


@pytest.mark.asyncio
async def test_authorization_basic(db: DatabaseTestUtils):
    await db.given(
        [
            default_user(),
            default_algorithm(),
            default_role(),
            default_rule(),
            default_authorization(),
        ]
    )

    authorization_repository = AuthorizationRepository(session=db.session)
    results = await authorization_repository.find_by_user(UUID(default_auth_user()["sub"]))

    assert results == [
        (
            AuthorizationResource.ORGANIZATION_INFO,
            [AuthorizationVerb.CREATE, AuthorizationVerb.READ],
            AuthorizationType.ORGANIZATION,
            1,
        )
    ]
