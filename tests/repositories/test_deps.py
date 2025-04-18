import pytest
from amt.core.exceptions import AMTRepositoryError
from amt.repositories.deps import (
    AsyncSessionWithCommitFlag,
    get_session,
    get_session_non_generator,
    transaction_context,
)
from pytest_mock import MockerFixture
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_get_session():
    session_generator = get_session()
    session = await anext(session_generator)
    assert isinstance(session, AsyncSession)

    # Clean up by consuming the rest of the generator
    try:  # noqa
        await session_generator.aclose()
    except StopAsyncIteration:
        pass


@pytest.mark.asyncio
async def test_get_session_non_generator():
    session = await get_session_non_generator()
    assert isinstance(session, AsyncSession)
    assert "id" in session.info


@pytest.mark.asyncio
async def test_transaction_context_commit(mocker: MockerFixture):
    # Given
    session = AsyncSessionWithCommitFlag()
    session.should_commit = True
    commit_mock = mocker.patch.object(session, "commit")

    # When
    async with transaction_context(session) as tx_session:
        assert tx_session is session

    # Then
    commit_mock.assert_called_once()


@pytest.mark.asyncio
async def test_transaction_context_dirty_no_commit(mocker: MockerFixture):
    # Given
    session = AsyncSessionWithCommitFlag()
    session.should_commit = False

    # Mock dirty property to return True
    mocker.patch.object(AsyncSessionWithCommitFlag, "dirty", new_callable=mocker.PropertyMock, return_value=True)

    commit_mock = mocker.patch.object(session, "commit")
    logger_mock = mocker.patch("amt.repositories.deps.logger.warning")

    # When
    async with transaction_context(session) as tx_session:
        assert tx_session is session

    # Then
    commit_mock.assert_not_called()
    logger_mock.assert_called_once_with(
        "Session changes detected, but no commit flag found. This is undesirable, check your code."
    )


@pytest.mark.asyncio
async def test_transaction_context_new_no_commit(mocker: MockerFixture):
    # Given
    session = AsyncSessionWithCommitFlag()
    session.should_commit = False

    # Mock new property to return True
    mocker.patch.object(AsyncSessionWithCommitFlag, "dirty", new_callable=mocker.PropertyMock, return_value=False)
    mocker.patch.object(AsyncSessionWithCommitFlag, "new", new_callable=mocker.PropertyMock, return_value=True)

    commit_mock = mocker.patch.object(session, "commit")
    logger_mock = mocker.patch("amt.repositories.deps.logger.warning")

    # When
    async with transaction_context(session) as tx_session:
        assert tx_session is session

    # Then
    commit_mock.assert_not_called()
    logger_mock.assert_called_once_with(
        "Session changes detected, but no commit flag found. This is undesirable, check your code."
    )


@pytest.mark.asyncio
async def test_transaction_context_deleted_no_commit(mocker: MockerFixture):
    # Given
    session = AsyncSessionWithCommitFlag()
    session.should_commit = False

    # Mock deleted property to return True
    mocker.patch.object(AsyncSessionWithCommitFlag, "dirty", new_callable=mocker.PropertyMock, return_value=False)
    mocker.patch.object(AsyncSessionWithCommitFlag, "new", new_callable=mocker.PropertyMock, return_value=False)
    mocker.patch.object(AsyncSessionWithCommitFlag, "deleted", new_callable=mocker.PropertyMock, return_value=True)

    commit_mock = mocker.patch.object(session, "commit")
    logger_mock = mocker.patch("amt.repositories.deps.logger.warning")

    # When
    async with transaction_context(session) as tx_session:
        assert tx_session is session

    # Then
    commit_mock.assert_not_called()
    logger_mock.assert_called_once_with(
        "Session changes detected, but no commit flag found. This is undesirable, check your code."
    )


@pytest.mark.asyncio
async def test_transaction_context_sqlalchemy_error(mocker: MockerFixture):
    # Given
    session = AsyncSessionWithCommitFlag()
    session.should_commit = True
    rollback_mock = mocker.patch.object(session, "rollback")
    commit_mock = mocker.patch.object(session, "commit", side_effect=SQLAlchemyError("Test error"))
    logger_mock = mocker.patch("amt.repositories.deps.logger.exception")

    # When/Then
    with pytest.raises(AMTRepositoryError):
        async with transaction_context(session) as tx_session:
            assert tx_session is session

    # Verify the rollback was called and the exception was logged
    commit_mock.assert_called_once()
    rollback_mock.assert_called_once()
    logger_mock.assert_called_once_with("Failed to commit transaction, rolling back session changes.")


@pytest.mark.asyncio
async def test_transaction_context_sqlalchemy_error_no_commit(mocker: MockerFixture):
    # Given
    session = AsyncSessionWithCommitFlag()
    session.should_commit = False
    rollback_mock = mocker.patch.object(session, "rollback")

    # When/Then
    with pytest.raises(AMTRepositoryError):
        async with transaction_context(session) as _:
            raise SQLAlchemyError("Test error")

    # Verify the rollback was not called because should_commit is False
    rollback_mock.assert_not_called()


@pytest.mark.asyncio
async def test_async_session_with_commit_flag():
    # Given
    session = AsyncSessionWithCommitFlag()

    # When/Then
    assert session.should_commit is False

    # Set should_commit to True
    session.should_commit = True
    assert session.should_commit is True
