import logging

import pytest
from amt.api.organization_filter_options import OrganizationFilterOptions
from amt.models import Organization
from amt.repositories.organizations import OrganizationsRepository
from tests.constants import default_organization, default_user
from tests.database_test_utils import DatabaseTestUtils

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_find_by(db: DatabaseTestUtils):
    await db.given([default_user(), default_organization(name="ZZZZZ", slug="zzzzz")])
    organization_repository = OrganizationsRepository(db.get_session())

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
async def test_find_by_as_count(db: DatabaseTestUtils):
    await db.given([default_user(), default_organization(name="ZZZZZ", slug="zzzzz")])
    organization_repository = OrganizationsRepository(db.get_session())
    organizations_count = await organization_repository.find_by_as_count(search="default")
    assert organizations_count == 1


@pytest.mark.asyncio
async def test_save(db: DatabaseTestUtils):
    await db.given([default_user()])
    organization_repository = OrganizationsRepository(db.get_session())
    new_organization = Organization(name="New organization", slug="new-organization", created_by_id=default_user().id)
    organization = await organization_repository.save(new_organization)
    assert organization.id == 2


@pytest.mark.asyncio
async def test_find_by_slug(db: DatabaseTestUtils):
    await db.given([default_user()])
    organization_repository = OrganizationsRepository(db.get_session())
    organization = await organization_repository.find_by_slug("default-organization")
    assert organization.name == "default organization"


@pytest.mark.asyncio
async def test_find_by_id(db: DatabaseTestUtils):
    await db.given([default_user()])
    organization_repository = OrganizationsRepository(db.get_session())
    organization = await organization_repository.find_by_id(1)
    assert organization.name == "default organization"


@pytest.mark.asyncio
async def test_find_by_id_and_user_id(db: DatabaseTestUtils):
    await db.given([default_user()])
    organization_repository = OrganizationsRepository(db.get_session())
    organization = await organization_repository.find_by_id_and_user_id(user_id=default_user().id, organization_id=1)
    assert organization.name == "default organization"


@pytest.mark.asyncio
async def test_remove_user(db: DatabaseTestUtils):
    await db.given([default_user()])
    organization_repository = OrganizationsRepository(db.get_session())
    organization = await organization_repository.find_by_id_and_user_id(user_id=default_user().id, organization_id=1)
    organization_updated = await organization_repository.remove_user(
        organization=organization,
        user=organization.users[0],  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    )
    assert len(organization_updated.users) == 0  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
