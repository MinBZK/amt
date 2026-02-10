import tempfile
from pathlib import Path

import pytest
from amt.core.session_store import InMemorySessionStore
from amt.middleware.session import ServerSideSessionMiddleware
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.staticfiles import StaticFiles


async def get_session(request: Request) -> JSONResponse:
    return JSONResponse({"session": dict(request.session), "session_id": request.scope.get("session_id")})


async def set_session(request: Request) -> JSONResponse:
    data = await request.json()
    for key, value in data.items():
        request.session[key] = value
    return JSONResponse({"status": "ok"})


async def clear_session(request: Request) -> JSONResponse:
    request.session.clear()
    return JSONResponse({"status": "cleared"})


def create_test_app(session_store: InMemorySessionStore) -> Starlette:
    routes = [
        Route("/get", get_session),
        Route("/set", set_session, methods=["POST"]),
        Route("/clear", clear_session, methods=["POST"]),
    ]
    app = Starlette(routes=routes)
    app.add_middleware(
        ServerSideSessionMiddleware,
        session_store=session_store,
        secret_key="test-secret-key",  # noqa: S106
    )
    return app


@pytest.mark.asyncio
async def test_new_session_returns_empty() -> None:
    # given
    store = InMemorySessionStore()
    app = create_test_app(store)

    # when
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/get")

    # then
    assert response.status_code == 200
    data = response.json()
    assert data["session"] == {}
    assert data["session_id"] is not None


@pytest.mark.asyncio
async def test_session_persists_across_requests() -> None:
    # given
    store = InMemorySessionStore()
    app = create_test_app(store)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # when
        set_response = await client.post("/set", json={"user": "test-user"})
        cookies = set_response.cookies

        get_response = await client.get("/get", cookies=cookies)

        # then
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["session"] == {"user": "test-user"}


@pytest.mark.asyncio
async def test_session_cookie_is_set() -> None:
    # given
    store = InMemorySessionStore()
    app = create_test_app(store)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # when
        response = await client.post("/set", json={"key": "value"})

        # then
        assert "session_id" in response.cookies


@pytest.mark.asyncio
async def test_clear_session_deletes_from_store() -> None:
    # given
    store = InMemorySessionStore()
    app = create_test_app(store)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # when
        set_response = await client.post("/set", json={"user": "test-user"})
        cookies = set_response.cookies

        await client.post("/clear", cookies=cookies)

        get_response = await client.get("/get", cookies=cookies)

        # then
        data = get_response.json()
        assert data["session"] == {}


@pytest.mark.asyncio
async def test_invalid_cookie_signature_creates_new_session() -> None:
    # given
    store = InMemorySessionStore()
    app = create_test_app(store)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # when
        response = await client.get("/get", cookies={"session_id": "invalid-tampered-cookie"})

        # then
        assert response.status_code == 200
        data = response.json()
        assert data["session"] == {}


@pytest.mark.asyncio
async def test_session_data_stored_in_memory_store() -> None:
    # given
    store = InMemorySessionStore()
    app = create_test_app(store)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # when
        set_response = await client.post("/set", json={"user": "test-user"})
        get_response = await client.get("/get", cookies=set_response.cookies)
        session_id = get_response.json()["session_id"]

        stored_data = await store.get(session_id)

        # then
        assert stored_data is not None
        assert stored_data["user"] == "test-user"


@pytest.mark.asyncio
async def test_no_session_cookie_on_empty_session() -> None:
    # given
    store = InMemorySessionStore()
    app = create_test_app(store)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # when
        response = await client.get("/get")

        # then
        assert "session_id" not in response.cookies


@pytest.mark.asyncio
async def test_https_only_adds_secure_flag() -> None:
    # given
    store = InMemorySessionStore()
    middleware = ServerSideSessionMiddleware(
        app=Starlette(),
        session_store=store,
        secret_key="test-secret-key",  # noqa: S106
        https_only=True,
    )

    # when/then
    assert "; secure" in middleware.security_flags


@pytest.mark.asyncio
async def test_domain_adds_domain_flag() -> None:
    # given
    store = InMemorySessionStore()
    middleware = ServerSideSessionMiddleware(
        app=Starlette(),
        session_store=store,
        secret_key="test-secret-key",  # noqa: S106
        domain="example.com",
    )

    # when/then
    assert "; domain=example.com" in middleware.security_flags


@pytest.mark.asyncio
async def test_excluded_paths_skip_session() -> None:
    # given
    store = InMemorySessionStore()
    routes = [Route("/get", get_session), Route("/health", get_session)]
    app = Starlette(routes=routes)
    app.add_middleware(
        ServerSideSessionMiddleware,
        session_store=store,
        secret_key="test-secret-key",  # noqa: S106
        exclude_paths=["/health"],
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # when
        response = await client.get("/health")

        # then
        assert response.status_code == 200
        assert "session_id" not in response.cookies


@pytest.mark.asyncio
async def test_static_paths_auto_discovered() -> None:
    # given
    with tempfile.TemporaryDirectory() as tmpdir:
        store = InMemorySessionStore()
        routes = [Route("/get", get_session)]
        app = Starlette(routes=routes)
        app.mount("/static", StaticFiles(directory=Path(tmpdir)), name="static")
        middleware = ServerSideSessionMiddleware(
            app=app,
            session_store=store,
            secret_key="test-secret-key",  # noqa: S106
            exclude_static_paths=True,
        )

        # when
        middleware._resolve_static_paths(app)  # pyright: ignore[reportPrivateUsage]

        # then
        assert "/static" in middleware.exclude_paths


@pytest.mark.asyncio
async def test_static_path_resolution_only_happens_once() -> None:
    # given
    with tempfile.TemporaryDirectory() as tmpdir:
        store = InMemorySessionStore()
        routes = [Route("/get", get_session)]
        app = Starlette(routes=routes)
        app.mount("/static", StaticFiles(directory=Path(tmpdir)), name="static")
        middleware = ServerSideSessionMiddleware(
            app=app,
            session_store=store,
            secret_key="test-secret-key",  # noqa: S106
            exclude_static_paths=True,
        )

        # when
        middleware._resolve_static_paths(app)  # pyright: ignore[reportPrivateUsage]
        middleware._resolve_static_paths(app)  # pyright: ignore[reportPrivateUsage]

        # then
        assert middleware.exclude_paths.count("/static") == 1


@pytest.mark.asyncio
async def test_static_path_resolution_skipped_when_flag_already_set() -> None:
    # given
    with tempfile.TemporaryDirectory() as tmpdir:
        store = InMemorySessionStore()
        routes = [Route("/get", get_session)]
        app = Starlette(routes=routes)
        app.mount("/static", StaticFiles(directory=Path(tmpdir)), name="static")
        middleware = ServerSideSessionMiddleware(
            app=app,
            session_store=store,
            secret_key="test-secret-key",  # noqa: S106
            exclude_static_paths=True,
        )
        middleware._static_paths_resolved = True  # pyright: ignore[reportPrivateUsage]

        # when
        middleware._resolve_static_paths(app)  # pyright: ignore[reportPrivateUsage]

        # then
        assert "/static" not in middleware.exclude_paths


@pytest.mark.asyncio
async def test_static_path_resolution_skipped_when_exclude_static_paths_false() -> None:
    # given
    with tempfile.TemporaryDirectory() as tmpdir:
        store = InMemorySessionStore()
        routes = [Route("/get", get_session)]
        app = Starlette(routes=routes)
        app.mount("/static", StaticFiles(directory=Path(tmpdir)), name="static")
        middleware = ServerSideSessionMiddleware(
            app=app,
            session_store=store,
            secret_key="test-secret-key",  # noqa: S106
            exclude_static_paths=False,
        )

        # when
        middleware._resolve_static_paths(app)  # pyright: ignore[reportPrivateUsage]

        # then
        assert "/static" not in middleware.exclude_paths


@pytest.mark.asyncio
async def test_static_path_resolution_handles_app_without_routes() -> None:
    # given
    store = InMemorySessionStore()

    async def simple_app(scope: dict[str, object], receive: object, send: object) -> None:
        pass

    middleware = ServerSideSessionMiddleware(
        app=simple_app,  # pyright: ignore[reportArgumentType]
        session_store=store,
        secret_key="test-secret-key",  # noqa: S106
        exclude_static_paths=True,
    )

    # when
    middleware._resolve_static_paths(simple_app)  # pyright: ignore[reportPrivateUsage, reportArgumentType]

    # then
    assert middleware._static_paths_resolved is True  # pyright: ignore[reportPrivateUsage]
    assert middleware.exclude_paths == []


@pytest.mark.asyncio
async def test_non_http_scope_passes_through() -> None:
    # given
    store = InMemorySessionStore()
    received_scope: dict[str, object] = {}

    async def capture_app(scope: dict[str, object], receive: object, send: object) -> None:
        received_scope.update(scope)

    middleware = ServerSideSessionMiddleware(
        app=capture_app,  # pyright: ignore[reportArgumentType]
        session_store=store,
        secret_key="test-secret-key",  # noqa: S106
    )

    # when
    await middleware({"type": "lifespan"}, None, None)  # type: ignore[arg-type]

    # then
    assert received_scope.get("type") == "lifespan"
    assert "session" not in received_scope


@pytest.mark.asyncio
async def test_expired_session_cookie_creates_new_session() -> None:
    # given
    store = InMemorySessionStore()
    app = create_test_app(store)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # when - set a session and then expire it in the store
        set_response = await client.post("/set", json={"user": "test-user"})
        cookies = set_response.cookies
        get_response = await client.get("/get", cookies=cookies)
        session_id = get_response.json()["session_id"]

        # simulate session expiry by deleting from store
        await store.delete(session_id)

        # when - request with expired session cookie
        new_response = await client.get("/get", cookies=cookies)

        # then - should get a new session
        new_data = new_response.json()
        assert new_data["session"] == {}
        assert new_data["session_id"] != session_id
