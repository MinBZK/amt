import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from pathlib import Path

import jinja_roos_components
from authlib.integrations.starlette_client import OAuth  # type: ignore
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from prometheus_client import Gauge  # pyright: ignore[reportMissingImports]
from prometheus_fastapi_instrumentator import Instrumentator  # pyright: ignore[reportMissingImports]

from amt.api.main import api_router
from amt.core.config import PROJECT_DESCRIPTION, PROJECT_NAME, VERSION, get_settings
from amt.core.db import check_db, get_engine, init_db
from amt.core.exception_handlers import general_exception_handler as amt_general_exception_handler
from amt.core.exception_handlers import redirect_exception_handler
from amt.core.exceptions import AMTRedirectError
from amt.core.log import configure_logging
from amt.core.session_store import InMemorySessionStore, SessionStore
from amt.utils.mask import Mask

from .api.http_browser_caching import static_files
from .middleware.authorization import AuthorizationMiddleware
from .middleware.csrf import CSRFMiddleware, CSRFMiddlewareExceptionHandler
from .middleware.htmx import HTMXMiddleware
from .middleware.route_logging import RequestLoggingMiddleware
from .middleware.security import SecurityMiddleware
from .middleware.session import ServerSideSessionMiddleware

configure_logging(
    get_settings().LOGGING_LEVEL,
    get_settings().LOGGING_CONFIG,
    get_settings().LOG_TO_FILE,
    get_settings().LOGFILE_LOCATION,
)

logger = logging.getLogger(__name__)

_db_pool_checked_in = Gauge("db_pool_checked_in", "DB connections available in pool")  # pyright: ignore[reportUnknownVariableType]
_db_pool_checked_out = Gauge("db_pool_checked_out", "DB connections currently in use")  # pyright: ignore[reportUnknownVariableType]
_db_pool_overflow = Gauge("db_pool_overflow", "DB connections beyond pool_size")  # pyright: ignore[reportUnknownVariableType]

STATIC_DIR_ROOS = Path(jinja_roos_components.__file__).parent / "static" / "roos" / "dist"


async def cleanup_sessions_task(session_store: SessionStore, interval: int) -> None:
    """Background task to periodically cleanup expired sessions."""
    while True:
        try:
            await asyncio.sleep(interval)
            expired_count = await session_store.cleanup_expired()
            active_count = await session_store.count()
            logger.info(f"Session stats: {active_count} active, {expired_count} expired and removed")
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Error during session cleanup")


# todo(berry): move lifespan to own file
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    mask = Mask(mask_keywords=["database_uri"])
    await check_db()
    await init_db()
    logger.info(f"Starting {PROJECT_NAME} version {VERSION}")
    logger.info(f"Settings: {mask.secrets(get_settings().model_dump())}")

    cleanup_task = asyncio.create_task(
        cleanup_sessions_task(app.state.session_store, get_settings().SESSION_CLEANUP_INTERVAL_SECONDS)
    )

    yield

    cleanup_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cleanup_task
    await app.state.session_store.close()

    logger.info(f"Stopping application {PROJECT_NAME} version {VERSION}")
    logging.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        title=PROJECT_NAME,
        summary=PROJECT_DESCRIPTION,
        version=VERSION,
        openapi_url=None,
        default_response_class=HTMLResponse,
        debug=get_settings().DEBUG,
    )

    session_store = InMemorySessionStore(default_ttl_seconds=get_settings().SESSION_TTL_SECONDS)
    app.state.session_store = session_store

    app.add_middleware(AuthorizationMiddleware)
    app.add_middleware(
        ServerSideSessionMiddleware,
        session_store=session_store,
        secret_key=get_settings().SECRET_KEY,
        session_cookie=get_settings().SESSION_COOKIE_NAME,
        max_age=get_settings().SESSION_TTL_SECONDS,
        https_only=get_settings().SESSION_COOKIE_SECURE,
        exclude_paths=["/health"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(CSRFMiddlewareExceptionHandler)
    app.add_middleware(HTMXMiddleware)
    app.add_middleware(SecurityMiddleware)
    # ProxyHeadersMiddleware must be last (runs first) to set correct scheme from X-Forwarded-Proto
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])  # type: ignore[arg-type]

    oauth = OAuth()
    app.state.oauth = oauth

    oauth.register(  # type: ignore
        name="keycloak",
        client_id=get_settings().OIDC_CLIENT_ID,
        client_secret=get_settings().OIDC_CLIENT_SECRET,
        server_metadata_url=get_settings().OIDC_DISCOVERY_URL,
        client_kwargs={"scope": "openid profile email"},
    )

    app.mount("/static", static_files, name="static")

    @app.exception_handler(AMTRedirectError)
    async def amt_redirect_exception_handler(request: Request, exc: AMTRedirectError) -> RedirectResponse:  # type: ignore[reportUnusedFunction]
        return await redirect_exception_handler(request, exc)

    @app.exception_handler(StarletteHTTPException)
    async def HTTPException_exception_handler(request: Request, exc: Exception) -> HTMLResponse:  # type: ignore
        return await amt_general_exception_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: Exception) -> HTMLResponse:  # type: ignore
        return await amt_general_exception_handler(request, exc)

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> HTMLResponse:  # type: ignore
        return await amt_general_exception_handler(request, exc)

    app.include_router(api_router)

    def db_pool_metrics(info: Any) -> None:  # noqa: ANN401  # pyright: ignore[reportUnknownParameterType]
        pool = get_engine().pool  # pyright: ignore[reportUnknownMemberType]
        _db_pool_checked_in.set(pool.checkedin())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
        _db_pool_checked_out.set(pool.checkedout())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
        _db_pool_overflow.set(pool.overflow())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]

    instrumentator = Instrumentator(excluded_handlers=["/health", "/metrics"])  # pyright: ignore[reportUnknownVariableType]
    instrumentator.add(db_pool_metrics)  # pyright: ignore[reportUnknownMemberType]
    instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)  # pyright: ignore[reportUnknownMemberType]

    return app


app = create_app()
