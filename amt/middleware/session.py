import logging
import uuid

import itsdangerous
from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from amt.core.session_store import SessionStore

logger = logging.getLogger(__name__)


class ServerSideSessionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        session_store: SessionStore,
        secret_key: str,
        session_cookie: str = "session_id",
        max_age: int = 60 * 60,
        path: str = "/",
        same_site: str = "lax",
        https_only: bool = False,
        domain: str | None = None,
        exclude_paths: list[str] | None = None,
        exclude_static_paths: bool = True,
    ) -> None:
        self.app = app
        self.session_store = session_store
        self.signer = itsdangerous.TimestampSigner(secret_key)
        self.session_cookie = session_cookie
        self.max_age = max_age
        self.path = path
        self.exclude_paths = exclude_paths or []
        self.exclude_static_paths = exclude_static_paths
        self._static_paths_resolved = False
        self.security_flags = "httponly; samesite=" + same_site
        if https_only:
            self.security_flags += "; secure"
        if domain is not None:
            self.security_flags += f"; domain={domain}"

    def _build_cookie_header(self, value: str, clear: bool = False) -> str:
        if clear:
            return (
                f"{self.session_cookie}=; path={self.path}; "
                f"expires=Thu, 01 Jan 1970 00:00:00 GMT; {self.security_flags}"
            )
        return f"{self.session_cookie}={value}; path={self.path}; Max-Age={self.max_age}; {self.security_flags}"

    async def _load_session(self, connection: HTTPConnection) -> tuple[str, dict[str, object], bool]:
        """Load session from cookie. Returns (session_id, data, had_session_on_arrival)."""
        if self.session_cookie not in connection.cookies:
            return str(uuid.uuid4()), {}, False

        signed_id = connection.cookies[self.session_cookie].encode("utf-8")
        try:
            session_id = self.signer.unsign(signed_id, max_age=self.max_age).decode("utf-8")
        except itsdangerous.BadSignature:
            logger.warning("Invalid session cookie signature - possible tampering or secret key mismatch")
            return str(uuid.uuid4()), {}, False

        session_data = await self.session_store.get(session_id)
        if session_data is not None:
            return session_id, session_data, True

        return str(uuid.uuid4()), {}, False

    def _resolve_static_paths(self, app: ASGIApp) -> None:
        """Discover static file mount paths from the app routes."""
        if self._static_paths_resolved or not self.exclude_static_paths:
            return

        if hasattr(app, "routes"):
            for route in app.routes:  # type: ignore[attr-defined]
                is_static_mount = isinstance(route, Mount) and isinstance(route.app, StaticFiles)
                if is_static_mount and route.path not in self.exclude_paths:
                    self.exclude_paths.append(route.path)

        self._static_paths_resolved = True

    def _is_excluded_path(self, path: str) -> bool:
        return any(path.startswith(excluded) for excluded in self.exclude_paths)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        self._resolve_static_paths(scope.get("app", self.app))

        path = scope.get("path", "")
        if self._is_excluded_path(path):
            scope["session"] = {}
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        session_id, session_data, had_session_on_arrival = await self._load_session(connection)
        scope["session"] = session_data
        scope["session_id"] = session_id

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                current_session: dict[str, object] = scope.get("session", {})
                headers = MutableHeaders(scope=message)

                session_has_data = bool(current_session)
                session_is_empty = not current_session
                user_logged_out = had_session_on_arrival and session_is_empty

                if session_has_data:
                    # Active session: save to store and set/refresh cookie
                    await self.session_store.set(session_id, current_session, self.max_age)
                    signed_id = self.signer.sign(session_id.encode("utf-8")).decode("utf-8")
                    headers.append("Set-Cookie", self._build_cookie_header(signed_id))
                elif user_logged_out:
                    # User logged out: delete from store and clear cookie
                    await self.session_store.delete(session_id)
                    headers.append("Set-Cookie", self._build_cookie_header("", clear=True))
                else:
                    # Anonymous user: no action needed
                    pass

            await send(message)

        await self.app(scope, receive, send_wrapper)
