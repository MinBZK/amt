import logging
from datetime import datetime, timedelta

import pytest
from amt.api.organization_filter_options import OrganizationFilterOptions
from amt.core.exceptions import AMTRepositoryError
from amt.models import Organization
from amt.repositories.organizations import OrganizationsRepository
from tests.constants import default_organization, default_user
from tests.database_test_utils import DatabaseTestUtils

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_find_by(db: DatabaseTestUtils):
    await db.given([default_user(), default_organization(), default_organization(name="ZZZZZ", slug="zzzzz")])
    organization_repository = OrganizationsRepository(db.get_session())
    await db.init_authorizations_and_roles()

    organizations = await organization_repository.find_by(sort={"name": "ascending"})
    assert organizations[0].name == "default organization"
    assert organizations[1].name == "ZZZZZ"

    organizations = await organization_repository.find_by(sort={"name": "descending"})
    assert organizations[0].name == "ZZZZZ"
    assert organizations[1].name == "default organization"

    organizations = await organization_repository.find_by(
        filters={"organization-type": OrganizationFilterOptions.MY_ORGANIZATIONS.value}, user_id=default_user().id
    )
    assert organizations[0].name == "default organization"

    organizations = await organization_repository.find_by(search="default")
    assert organizations[0].name == "default organization"

    organizations = await organization_repository.find_by(search="no results")
    assert len(organizations) == 0

    organizations = await organization_repository.find_by(search="default", skip=10, limit=100)
    assert len(organizations) == 0


@pytest.mark.asyncio
async def test_find_by_sort_by_last_update(db: DatabaseTestUtils):
    # given
    now = datetime.now()  # noqa DTZ005
    older_time = now - timedelta(days=7)

    org1 = default_organization(name="Newer org", slug="newer-org")
    org1.modified_at = now

    org2 = default_organization(name="Older org", slug="older-org")
    org2.modified_at = older_time

    await db.given([default_user(), org1, org2])
    organization_repository = OrganizationsRepository(db.get_session())

    # when
    organizations_asc = await organization_repository.find_by(sort={"last_update": "ascending"})
    organizations_desc = await organization_repository.find_by(sort={"last_update": "descending"})

    # then
    assert organizations_asc[0].name == "Older org"
    assert organizations_asc[1].name == "Newer org"

    assert organizations_desc[0].name == "Newer org"
    assert organizations_desc[1].name == "Older org"


@pytest.mark.asyncio
async def test_find_by_as_count(db: DatabaseTestUtils):
    await db.given([default_user(), default_organization(), default_organization(name="ZZZZZ", slug="zzzzz")])
    organization_repository = OrganizationsRepository(db.get_session())
    organizations_count = await organization_repository.find_by_as_count(search="default")
    assert organizations_count == 1


@pytest.mark.asyncio
async def test_save(db: DatabaseTestUtils):
    await db.given([default_user(), default_organization()])
    organization_repository = OrganizationsRepository(db.get_session())
    new_organization = Organization(name="New organization", slug="new-organization", created_by_id=default_user().id)
    organization = await organization_repository.save(new_organization)
    assert organization.id == 2


@pytest.mark.asyncio
async def test_find_by_slug(db: DatabaseTestUtils):
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()
    organization_repository = OrganizationsRepository(db.get_session())
    organization = await organization_repository.find_by_slug("default-organization")
    assert organization.name == "default organization"


@pytest.mark.asyncio
async def test_find_by_slug_not_found(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization()])
    organization_repository = OrganizationsRepository(db.get_session())

    # when / then
    with pytest.raises(AMTRepositoryError):
        await organization_repository.find_by_slug("non-existent-slug")


@pytest.mark.asyncio
async def test_find_by_id(db: DatabaseTestUtils):
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()
    organization_repository = OrganizationsRepository(db.get_session())
    organization = await organization_repository.find_by_id(1)
    assert organization.name == "default organization"


@pytest.mark.asyncio
async def test_find_by_id_not_found(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization()])
    organization_repository = OrganizationsRepository(db.get_session())

    # when / then
    with pytest.raises(AMTRepositoryError):
        await organization_repository.find_by_id(999)


@pytest.mark.asyncio
async def test_find_by_id_and_user_id(db: DatabaseTestUtils):
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()
    organization_repository = OrganizationsRepository(db.get_session())
    organization = await organization_repository.find_by_id_and_user_id(user_id=default_user().id, organization_id=1)
    assert organization.name == "default organization"


@pytest.mark.asyncio
async def test_find_by_id_and_user_id_not_found(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization()])
    await db.init_authorizations_and_roles()
    organization_repository = OrganizationsRepository(db.get_session())

    # when / then
    with pytest.raises(AMTRepositoryError):
        await organization_repository.find_by_id_and_user_id(user_id=default_user().id, organization_id=999)


@pytest.mark.asyncio
async def test_get_by_user(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization(), default_organization(name="Second org", slug="second-org")])
    await db.init_authorizations_and_roles()
    organization_repository = OrganizationsRepository(db.get_session())

    # when
    organizations = await organization_repository.get_by_user(user_id=default_user().id)

    # then
    assert len(organizations) == 1
    assert organizations[0].name == "default organization"
