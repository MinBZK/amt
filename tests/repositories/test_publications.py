import datetime

import pytest
from amt.core.exceptions import AMTRepositoryError
from amt.models import Publication
from amt.repositories.publications import PublicationsRepository
from tests.constants import default_algorithm, default_organization, default_user
from tests.database_test_utils import DatabaseTestUtils


@pytest.mark.asyncio
async def test_find_by_id(db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("test_algorithm")])
    publication = Publication(
        last_updated=datetime.datetime.now(tz=None),  # noqa: DTZ005
        algorithm_id=1,
        lars="LARS123",
        organization_code="ORG1",
    )
    await db.given([publication])

    publications_repository = PublicationsRepository(session=db.session)

    # when
    result = await publications_repository.find_by_id(1)

    # then
    assert result.lars == "LARS123"
    assert result.organization_code == "ORG1"


@pytest.mark.asyncio
async def test_find_by_id_not_found(db: DatabaseTestUtils) -> None:
    # given
    publications_repository = PublicationsRepository(session=db.session)

    # when/then
    with pytest.raises(AMTRepositoryError):
        await publications_repository.find_by_id(999)


@pytest.mark.asyncio
async def test_find_by_algorithm_id(db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("test_algorithm")])
    publication = Publication(
        last_updated=datetime.datetime.now(tz=None),  # noqa: DTZ005
        algorithm_id=1,
        lars="LARS456",
        organization_code="ORG2",
    )
    await db.given([publication])

    publications_repository = PublicationsRepository(session=db.session)

    # when
    result = await publications_repository.find_by_algorithm_id(1)

    # then
    assert result is not None
    assert result.lars == "LARS456"


@pytest.mark.asyncio
async def test_find_by_algorithm_id_not_found(db: DatabaseTestUtils) -> None:
    # given
    publications_repository = PublicationsRepository(session=db.session)

    # when
    result = await publications_repository.find_by_algorithm_id(999)

    # then
    assert result is None


@pytest.mark.asyncio
async def test_save(db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("test_algorithm")])
    publications_repository = PublicationsRepository(session=db.session)
    publication = Publication(
        last_updated=datetime.datetime.now(tz=None),  # noqa: DTZ005
        algorithm_id=1,
        lars="LARS789",
        organization_code="ORG3",
    )

    # when
    result = await publications_repository.save(publication)

    # then
    assert result.id is not None
    assert result.lars == "LARS789"
    assert db.session.should_commit is True


@pytest.mark.asyncio
async def test_delete_by_algorithm_id(db: DatabaseTestUtils) -> None:
    # given
    await db.given([default_user(), default_organization(), default_algorithm("test_algorithm")])
    publication = Publication(
        last_updated=datetime.datetime.now(tz=None),  # noqa: DTZ005
        algorithm_id=1,
        lars="12345678",
        organization_code="ORG_DEL",
    )
    await db.given([publication])

    publications_repository = PublicationsRepository(session=db.session)

    # when
    await publications_repository.delete_by_algorithm_id(1)

    # then
    result = await publications_repository.find_by_algorithm_id(1)
    assert result is None
    assert db.session.should_commit is True


@pytest.mark.asyncio
async def test_delete_by_algorithm_id_not_found(db: DatabaseTestUtils) -> None:
    # given
    publications_repository = PublicationsRepository(session=db.session)

    # when
    await publications_repository.delete_by_algorithm_id(999)

    # then (no exception should be raised)
    assert db.session.should_commit is False
