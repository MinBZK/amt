import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from amt.api.main import api_router
from amt.core.config import PROJECT_DESCRIPTION, PROJECT_NAME, VERSION, get_settings
from amt.core.db import check_db, init_db
from amt.core.exception_handlers import (
    http_exception_handler as amt_http_exception_handler,
)
from amt.core.exception_handlers import (
    validation_exception_handler as amt_validation_exception_handler,
)
from amt.core.log import configure_logging
from amt.utils.mask import Mask

from .api.http_browser_caching import static_files
from .middleware.csrf import CSRFMiddleware, CSRFMiddlewareExceptionHandler
from .middleware.htmx import HTMXMiddleware
from .middleware.route_logging import RequestLoggingMiddleware

configure_logging(get_settings().LOGGING_LEVEL, get_settings().LOGGING_CONFIG)

logger = logging.getLogger(__name__)


# todo(berry): move lifespan to own file
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    mask = Mask(mask_keywords=["database_uri"])
    check_db()
    init_db()
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

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(CSRFMiddlewareExceptionHandler)
    app.add_middleware(HTMXMiddleware)

    app.mount("/static", static_files, name="static")

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse:  # type: ignore
        return await amt_http_exception_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> HTMLResponse:  # type: ignore
        return await amt_validation_exception_handler(request, exc)

    app.include_router(api_router)

    return app


app = create_app()
