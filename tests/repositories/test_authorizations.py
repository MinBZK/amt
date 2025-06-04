from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from amt.core.authorization import AuthorizationType
from amt.core.exceptions import AMTRepositoryError
from amt.models import Authorization
from amt.repositories.authorizations import AuthorizationRepository
from tests.constants import (
    default_algorithm,
    default_auth_user,
    default_authorization,
    default_organization,
    default_user,
)
from tests.database_test_utils import DatabaseTestUtils, get_auth_setup_sql


@pytest.mark.asyncio
async def test_authorization_basic(db: DatabaseTestUtils):
    # given
    await db.given(
        [
            default_user(),
            default_organization(),
            default_algorithm(),
        ]
    )
    await db.init_authorizations_and_roles()

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    results = await authorization_repository.find_by_user(UUID(default_auth_user()["sub"]))

    # then
    assert len(results) == 6


@pytest.mark.asyncio
async def test_get_user(db: DatabaseTestUtils):
    # given
    user = default_user()
    await db.given([user])

    users_repository = MagicMock()
    users_repository.find_by_id = AsyncMock()
    users_repository.find_by_id.return_value = user

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=users_repository,
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    result = await authorization_repository.get_user(user.id)

    # then
    assert result == user
    users_repository.find_by_id.assert_called_once_with(user.id)


@pytest.mark.asyncio
async def test_get_role_for_user(db: DatabaseTestUtils):
    # given
    user = default_user()
    await db.given([user])

    # Initialize auth roles without the default authorizations
    await db.given_sql(get_auth_setup_sql())

    # Add a specific authorization for this test
    auth = default_authorization(user_id=str(user.id), role_id=1, type=AuthorizationType.ORGANIZATION, type_id=1)
    await db.given([auth])

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    result = await authorization_repository.get_role_for_user(UUID(str(user.id)), AuthorizationType.ORGANIZATION, 1)

    # then
    assert result is not None
    assert result.user_id == user.id
    assert result.role_id == 1
    assert result.type == AuthorizationType.ORGANIZATION
    assert result.type_id == 1


@pytest.mark.asyncio
async def test_get_role_for_user_not_found(db: DatabaseTestUtils):
    # given
    user = default_user()
    await db.given([user])

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    result = await authorization_repository.get_role_for_user(UUID(str(user.id)), AuthorizationType.ORGANIZATION, 1)

    # then
    assert result is None


@pytest.mark.asyncio
async def test_add_role_for_user_new(db: DatabaseTestUtils):
    # given
    user = default_user()
    await db.given([user])
    await db.init_authorizations_and_roles()

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    await authorization_repository.add_role_for_user(
        user_id=str(user.id), role_id=1, role_type=AuthorizationType.ORGANIZATION, type_id=1
    )

    # then
    auth = await authorization_repository.get_role_for_user(UUID(str(user.id)), AuthorizationType.ORGANIZATION, 1)
    assert auth is not None
    assert auth.user_id == user.id
    assert auth.role_id == 1
    assert auth.type == AuthorizationType.ORGANIZATION
    assert auth.type_id == 1


@pytest.mark.asyncio
async def test_add_role_for_user_update(db: DatabaseTestUtils):
    # given
    user = default_user()
    await db.given([user])

    # Initialize auth roles without the default authorizations
    await db.given_sql(get_auth_setup_sql())

    # Add a specific authorization for this test
    auth = default_authorization(user_id=str(user.id), role_id=1, type=AuthorizationType.ORGANIZATION, type_id=1)
    await db.given([auth])

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    await authorization_repository.add_role_for_user(
        user_id=str(user.id),
        role_id=2,  # Changed role ID
        role_type=AuthorizationType.ORGANIZATION,
        type_id=1,
    )

    # then
    updated_auth = await authorization_repository.get_role_for_user(
        UUID(str(user.id)), AuthorizationType.ORGANIZATION, 1
    )
    assert updated_auth is not None
    assert updated_auth.user_id == user.id
    assert updated_auth.role_id == 2  # Verify role ID was updated
    assert updated_auth.type == AuthorizationType.ORGANIZATION
    assert updated_auth.type_id == 1


@pytest.mark.asyncio
async def test_get_default_permissions():
    # given/when
    permissions = AuthorizationRepository.get_default_permissions()

    # then
    assert len(permissions) == 2
    assert permissions[0][0] == "organizations/"
    assert permissions[1][0] == "algorithms/"


@pytest.mark.asyncio
async def test_remove_algorithm_roles(db: DatabaseTestUtils):
    # given
    user = default_user()
    organization = default_organization()
    algorithm = default_algorithm()
    await db.given([user, organization, algorithm])
    await db.init_authorizations_and_roles()
    auth = default_authorization(
        user_id=str(user.id), role_id=4, type=AuthorizationType.ALGORITHM, type_id=algorithm.id
    )
    await db.given([auth])

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    await authorization_repository.remove_algorithm_roles(str(user.id), algorithm)

    # then
    result = await authorization_repository.get_role_for_user(
        UUID(str(user.id)), AuthorizationType.ALGORITHM, algorithm.id
    )
    assert result is None


@pytest.mark.asyncio
async def test_get_role_by_id(db: DatabaseTestUtils):
    # given
    await db.given_sql(get_auth_setup_sql())

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    role = await authorization_repository.get_role_by_id(1)

    # then
    assert role is not None
    assert role.id == 1
    assert role.name == "Organization Maintainer"


@pytest.mark.asyncio
async def test_get_role_by_id_not_found(db: DatabaseTestUtils):
    # given
    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    role = await authorization_repository.get_role_by_id(999)  # Non-existent role

    # then
    assert role is None


@pytest.mark.asyncio
async def test_get_role(db: DatabaseTestUtils):
    # given
    await db.given_sql(get_auth_setup_sql())

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    role = await authorization_repository.get_role("Organization Maintainer")

    # then
    assert role is not None
    assert role.id == 1
    assert role.name == "Organization Maintainer"


@pytest.mark.asyncio
async def test_get_role_not_found(db: DatabaseTestUtils):
    # given
    # Initialize roles first
    await db.given_sql(get_auth_setup_sql())

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when/then
    with pytest.raises(AMTRepositoryError):
        await authorization_repository.get_role("Non-existent Role")


@pytest.mark.asyncio
async def test_save(db: DatabaseTestUtils):
    # given
    user = default_user()
    await db.given([user])
    await db.init_authorizations_and_roles()

    authorization = Authorization(user_id=user.id, role_id=1, type=AuthorizationType.ORGANIZATION, type_id=1)

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    saved_auth = await authorization_repository.save(authorization)

    # then
    assert saved_auth.id is not None
    assert saved_auth.user_id == user.id
    assert saved_auth.role_id == 1
    assert saved_auth.type == AuthorizationType.ORGANIZATION
    assert saved_auth.type_id == 1


@pytest.mark.asyncio
async def test_find_by_user_and_type(db: DatabaseTestUtils):
    # given
    user = default_user()
    await db.given([user])

    # Initialize auth roles without the default authorizations
    await db.given_sql(get_auth_setup_sql())

    auth = default_authorization(user_id=str(user.id), role_id=1, type=AuthorizationType.ORGANIZATION, type_id=1)
    await db.given([auth])

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    result = await authorization_repository.find_by_user_and_type(str(user.id), 1, AuthorizationType.ORGANIZATION)

    # then
    assert result is not None
    assert result.user_id == user.id
    assert result.role_id == 1
    assert result.type == AuthorizationType.ORGANIZATION
    assert result.type_id == 1


@pytest.mark.asyncio
async def test_find_by_user_and_type_not_found(db: DatabaseTestUtils):
    # given
    user = default_user()
    await db.given([user])
    await db.given_sql(get_auth_setup_sql())

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when/then
    with pytest.raises(AMTRepositoryError):
        await authorization_repository.find_by_user_and_type(str(user.id), 1, AuthorizationType.ORGANIZATION)


@pytest.mark.asyncio
async def test_get_users_with_authorizations(db: DatabaseTestUtils):
    # given
    user = default_user()
    await db.given([user])

    # Initialize auth roles without the default authorizations
    await db.given_sql(get_auth_setup_sql())

    # Add a specific authorization for this test
    auth = default_authorization(user_id=str(user.id), role_id=1, type=AuthorizationType.ORGANIZATION, type_id=1)
    await db.given([auth])

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    results = await authorization_repository.get_users_with_authorizations(
        type_id=1, authorization_type=AuthorizationType.ORGANIZATION
    )

    # then
    assert len(results) == 1
    assert results[0][0].id == user.id
    assert results[0][1].type == AuthorizationType.ORGANIZATION
    assert results[0][1].type_id == 1
    assert results[0][1].role_id == 1
    assert results[0][2].id == 1
    assert results[0][2].name == "Organization Maintainer"


@pytest.mark.asyncio
async def test_find_all(db: DatabaseTestUtils):
    # given
    user1 = default_user()
    user2 = default_user(id="d4c4e1e8-ab21-4be3-b81c-eff75906421c", name="Another User")
    await db.given([user1, user2])

    # Initialize auth roles without the default authorizations
    await db.given_sql(get_auth_setup_sql())

    # Create organization with correct fields
    organization = default_organization(name="Test Organization", slug="test-org")
    # Set ID explicitly after creation
    organization.id = 1
    await db.given([organization])

    auth1 = default_authorization(user_id=str(user1.id), role_id=1, type=AuthorizationType.ORGANIZATION, type_id=1)
    auth2 = default_authorization(user_id=str(user2.id), role_id=2, type=AuthorizationType.ORGANIZATION, type_id=1)
    await db.given([auth1, auth2])

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    results = await authorization_repository.find_all()

    # then
    assert len(results) == 2

    # Test with filters
    filtered_results = await authorization_repository.find_all(
        filters={"type": AuthorizationType.ORGANIZATION, "type_id": 1}
    )
    assert len(filtered_results) == 2

    # Test with search
    search_results = await authorization_repository.find_all(search="Another")
    assert len(search_results) == 1
    assert search_results[0][0].name == "Another User"

    # Test with sort ascending
    sorted_results = await authorization_repository.find_all(sort={"name": "ascending"})
    assert len(sorted_results) == 2
    assert sorted_results[0][0].name == "Another User"
    assert sorted_results[1][0].name == "Default User"

    # Test with sort descending
    sorted_desc_results = await authorization_repository.find_all(sort={"name": "descending"})
    assert len(sorted_desc_results) == 2
    assert sorted_desc_results[0][0].name == "Default User"
    assert sorted_desc_results[1][0].name == "Another User"

    # Test with limit and skip
    limited_results = await authorization_repository.find_all(limit=1)
    assert len(limited_results) == 1

    skipped_results = await authorization_repository.find_all(skip=1, limit=1)
    assert len(skipped_results) == 1


@pytest.mark.asyncio
async def test_remove_all_roles(db: DatabaseTestUtils):
    # given
    user = default_user()
    organization = default_organization()
    algorithm1 = default_algorithm(name="algorithm1")
    algorithm2 = default_algorithm(name="algorithm2")
    await db.given([user, organization, algorithm1, algorithm2])

    # Initialize auth roles without the default authorizations
    await db.given_sql(get_auth_setup_sql())

    # Add organization role
    org_auth = default_authorization(
        user_id=str(user.id), role_id=1, type=AuthorizationType.ORGANIZATION, type_id=organization.id
    )

    # Add algorithm roles
    alg1_auth = default_authorization(
        user_id=str(user.id), role_id=4, type=AuthorizationType.ALGORITHM, type_id=algorithm1.id
    )
    alg2_auth = default_authorization(
        user_id=str(user.id), role_id=4, type=AuthorizationType.ALGORITHM, type_id=algorithm2.id
    )

    await db.given([org_auth, alg1_auth, alg2_auth])

    # Create a mock algorithms repository
    algorithms_repository = MagicMock()
    algorithms_repository.get_by_user_and_organization = AsyncMock()
    algorithms_repository.get_by_user_and_organization.return_value = [algorithm1, algorithm2]

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=algorithms_repository,
    )

    # Verify authorizations exist before removal
    org_role_before = await authorization_repository.get_role_for_user(
        UUID(str(user.id)), AuthorizationType.ORGANIZATION, organization.id
    )
    assert org_role_before is not None

    alg1_role_before = await authorization_repository.get_role_for_user(
        UUID(str(user.id)), AuthorizationType.ALGORITHM, algorithm1.id
    )
    assert alg1_role_before is not None

    alg2_role_before = await authorization_repository.get_role_for_user(
        UUID(str(user.id)), AuthorizationType.ALGORITHM, algorithm2.id
    )
    assert alg2_role_before is not None

    # when
    await authorization_repository.remove_all_roles(str(user.id), organization)

    # then
    algorithms_repository.get_by_user_and_organization.assert_called_once_with(UUID(str(user.id)), organization.id)

    # Verify all authorizations were removed
    org_role_after = await authorization_repository.get_role_for_user(
        UUID(str(user.id)), AuthorizationType.ORGANIZATION, organization.id
    )
    assert org_role_after is None

    alg1_role_after = await authorization_repository.get_role_for_user(
        UUID(str(user.id)), AuthorizationType.ALGORITHM, algorithm1.id
    )
    assert alg1_role_after is None

    alg2_role_after = await authorization_repository.get_role_for_user(
        UUID(str(user.id)), AuthorizationType.ALGORITHM, algorithm2.id
    )
    assert alg2_role_after is None


@pytest.mark.asyncio
async def test_get_by_id(db: DatabaseTestUtils):
    # given
    user = default_user()
    await db.given([user])

    # Initialize auth roles without the default authorizations
    await db.given_sql(get_auth_setup_sql())

    # Create organization with correct fields
    organization = default_organization(name="Test Organization", slug="test-org")
    # Set ID explicitly after creation
    organization.id = 1
    await db.given([organization])

    auth = default_authorization(user_id=str(user.id), role_id=1, type=AuthorizationType.ORGANIZATION, type_id=1)
    await db.given([auth])

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # Since we just inserted the authorization, we can use its ID directly
    auth_id = auth.id

    # when
    result = await authorization_repository.get_by_id(auth_id)

    # then
    assert result is not None
    assert result.id == auth_id
    assert result.user_id == user.id
    assert result.role_id == 1
    assert result.type == AuthorizationType.ORGANIZATION
    assert result.type_id == 1


@pytest.mark.asyncio
async def test_get_by_id_not_found(db: DatabaseTestUtils):
    # given
    await db.given_sql(get_auth_setup_sql())

    authorization_repository = AuthorizationRepository(
        session=db.session,
        users_repository=None,  # pyright: ignore[reportArgumentType]
        organizations_repository=None,  # pyright: ignore[reportArgumentType]
        algorithms_repository=None,  # pyright: ignore[reportArgumentType]
    )

    # when
    result = await authorization_repository.get_by_id(999)  # Non-existent authorization

    # then
    assert result is None
