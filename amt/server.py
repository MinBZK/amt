import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from authlib.integrations.starlette_client import OAuth  # type: ignore
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from amt.api.main import api_router
from amt.core.config import PROJECT_DESCRIPTION, PROJECT_NAME, VERSION, get_settings
from amt.core.db import check_db, init_db
from amt.core.exception_handlers import general_exception_handler as amt_general_exception_handler
from amt.core.log import configure_logging
from amt.utils.mask import Mask

from .api.http_browser_caching import static_files
from .middleware.authorization import AuthorizationMiddleware
from .middleware.csrf import CSRFMiddleware, CSRFMiddlewareExceptionHandler
from .middleware.htmx import HTMXMiddleware
from .middleware.route_logging import RequestLoggingMiddleware
from .middleware.security import SecurityMiddleware

configure_logging(
    get_settings().LOGGING_LEVEL,
    get_settings().LOGGING_CONFIG,
    get_settings().LOG_TO_FILE,
    get_settings().LOGFILE_LOCATION,
)

logger = logging.getLogger(__name__)


# todo(berry): move lifespan to own file
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    mask = Mask(mask_keywords=["database_uri"])
    await check_db()
    await init_db()
    logger.info(f"Starting {PROJECT_NAME} version {VERSION}")
    logger.info(f"Settings: {mask.secrets(get_settings().model_dump())}")
    yield

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

    app.add_middleware(AuthorizationMiddleware)
    app.add_middleware(SessionMiddleware, secret_key=get_settings().SECRET_KEY)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(CSRFMiddlewareExceptionHandler)
    app.add_middleware(HTMXMiddleware)
    app.add_middleware(SecurityMiddleware)

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

    return app


app = create_app()
