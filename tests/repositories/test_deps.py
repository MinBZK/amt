import pytest
from amt.repositories.deps import get_session, get_session_non_generator
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
