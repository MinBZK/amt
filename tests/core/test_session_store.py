import pytest
from amt.core.session_store import InMemorySessionStore


@pytest.mark.asyncio
async def test_set_and_get() -> None:
    # given
    store = InMemorySessionStore()
    session_id = "test-session"
    data = {"user": {"name": "test"}}

    # when
    await store.set(session_id, data)
    result = await store.get(session_id)

    # then
    assert result == data


@pytest.mark.asyncio
async def test_get_returns_none_for_nonexistent_session() -> None:
    # given
    store = InMemorySessionStore()

    # when
    result = await store.get("nonexistent")

    # then
    assert result is None


@pytest.mark.asyncio
async def test_get_returns_copy_not_reference() -> None:
    # given
    store = InMemorySessionStore()
    session_id = "test-session"
    data = {"key": "value"}
    await store.set(session_id, data)

    # when
    result = await store.get(session_id)
    result["key"] = "modified"  # type: ignore[index]
    original = await store.get(session_id)

    # then
    assert original == {"key": "value"}


@pytest.mark.asyncio
async def test_set_stores_copy_not_reference() -> None:
    # given
    store = InMemorySessionStore()
    session_id = "test-session"
    data = {"key": "value"}

    # when
    await store.set(session_id, data)
    data["key"] = "modified"
    result = await store.get(session_id)

    # then
    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_delete() -> None:
    # given
    store = InMemorySessionStore()
    session_id = "test-session"
    await store.set(session_id, {"key": "value"})

    # when
    await store.delete(session_id)
    result = await store.get(session_id)

    # then
    assert result is None


@pytest.mark.asyncio
async def test_delete_nonexistent_does_not_raise() -> None:
    # given
    store = InMemorySessionStore()

    # when/then
    await store.delete("nonexistent")


@pytest.mark.asyncio
async def test_touch_extends_ttl() -> None:
    # given
    store = InMemorySessionStore(default_ttl_seconds=100)
    session_id = "test-session"
    await store.set(session_id, {"key": "value"})
    original_expires_at = store._sessions[session_id].expires_at  # pyright: ignore[reportPrivateUsage]

    # when
    touched = await store.touch(session_id, ttl_seconds=200)
    new_expires_at = store._sessions[session_id].expires_at  # pyright: ignore[reportPrivateUsage]

    # then
    assert touched is True
    assert new_expires_at > original_expires_at


@pytest.mark.asyncio
async def test_touch_returns_false_for_nonexistent() -> None:
    # given
    store = InMemorySessionStore()

    # when
    result = await store.touch("nonexistent")

    # then
    assert result is False


@pytest.mark.asyncio
async def test_session_expires_after_ttl() -> None:
    # given
    store = InMemorySessionStore(default_ttl_seconds=100)
    session_id = "test-session"
    await store.set(session_id, {"key": "value"})

    # when - simulate expiry by setting expires_at to the past
    store._sessions[session_id].expires_at = 0  # pyright: ignore[reportPrivateUsage]
    result = await store.get(session_id)

    # then
    assert result is None


@pytest.mark.asyncio
async def test_cleanup_expired() -> None:
    # given
    store = InMemorySessionStore(default_ttl_seconds=100)
    await store.set("session1", {"key": "value1"})
    await store.set("session2", {"key": "value2"})

    # simulate expiry by setting expires_at to the past
    store._sessions["session1"].expires_at = 0  # pyright: ignore[reportPrivateUsage]
    store._sessions["session2"].expires_at = 0  # pyright: ignore[reportPrivateUsage]

    # when
    count = await store.cleanup_expired()

    # then
    assert count == 2


@pytest.mark.asyncio
async def test_cleanup_expired_does_not_remove_active_sessions() -> None:
    # given
    store = InMemorySessionStore(default_ttl_seconds=10)
    await store.set("active-session", {"key": "value"})

    # when
    count = await store.cleanup_expired()
    result = await store.get("active-session")

    # then
    assert count == 0
    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_close_clears_all_sessions() -> None:
    # given
    store = InMemorySessionStore()
    await store.set("session1", {"key": "value1"})
    await store.set("session2", {"key": "value2"})

    # when
    await store.close()
    result1 = await store.get("session1")
    result2 = await store.get("session2")

    # then
    assert result1 is None
    assert result2 is None


@pytest.mark.asyncio
async def test_count_returns_number_of_active_sessions() -> None:
    # given
    store = InMemorySessionStore()
    await store.set("session1", {"key": "value1"})
    await store.set("session2", {"key": "value2"})
    await store.set("session3", {"key": "value3"})

    # when
    count = await store.count()

    # then
    assert count == 3
