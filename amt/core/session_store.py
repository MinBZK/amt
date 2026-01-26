import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class SessionStore(ABC):
    """Abstract interface for session storage backends."""

    @abstractmethod
    async def get(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve session data by ID. Returns None if not found or expired."""
        ...

    @abstractmethod
    async def set(self, session_id: str, data: dict[str, Any], ttl_seconds: int | None = None) -> None:
        """Store session data with optional TTL."""
        ...

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete a session by ID."""
        ...

    @abstractmethod
    async def touch(self, session_id: str, ttl_seconds: int | None = None) -> bool:
        """Extend session TTL. Returns False if session does not exist."""
        ...

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Cleanup resources (called on shutdown)."""
        ...

    @abstractmethod
    async def count(self) -> int:
        """Return the number of active sessions."""
        ...


@dataclass
class SessionEntry:
    data: dict[str, Any]
    expires_at: float


class InMemorySessionStore(SessionStore):
    def __init__(self, default_ttl_seconds: int = 60 * 60) -> None:
        self._sessions: dict[str, SessionEntry] = {}
        self._default_ttl = default_ttl_seconds
        self._lock = asyncio.Lock()

    async def get(self, session_id: str) -> dict[str, Any] | None:
        async with self._lock:
            entry = self._sessions.get(session_id)
            if entry is None:
                return None
            if time.time() > entry.expires_at:
                del self._sessions[session_id]
                return None
            return entry.data.copy()

    async def set(self, session_id: str, data: dict[str, Any], ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        async with self._lock:
            self._sessions[session_id] = SessionEntry(data=data.copy(), expires_at=time.time() + ttl)

    async def delete(self, session_id: str) -> None:
        async with self._lock:
            self._sessions.pop(session_id, None)

    async def touch(self, session_id: str, ttl_seconds: int | None = None) -> bool:
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        async with self._lock:
            entry = self._sessions.get(session_id)
            if entry is None or time.time() > entry.expires_at:
                return False
            entry.expires_at = time.time() + ttl
            return True

    async def cleanup_expired(self) -> int:
        now = time.time()
        async with self._lock:
            expired = [sid for sid, entry in self._sessions.items() if now > entry.expires_at]
            for sid in expired:
                del self._sessions[sid]
            return len(expired)

    async def close(self) -> None:
        async with self._lock:
            self._sessions.clear()

    async def count(self) -> int:
        async with self._lock:
            return len(self._sessions)
