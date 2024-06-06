import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from tad.api.main import api_router
from tad.core.config import PROJECT_DESCRIPTION, PROJECT_NAME, VERSION, get_settings
from tad.core.db import check_db, init_db
from tad.core.exception_handlers import (
    http_exception_handler as tad_http_exception_handler,
)
from tad.core.exception_handlers import (
    validation_exception_handler as tad_validation_exception_handler,
)
from tad.core.log import configure_logging
from tad.utils.mask import Mask

from .middleware.route_logging import RequestLoggingMiddleware

configure_logging(get_settings().LOGGING_LEVEL, get_settings().LOGGING_CONFIG)

logger = logging.getLogger(__name__)


# todo(berry): move lifespan to own file
@asynccontextmanager
async def lifespan(app: FastAPI):
    mask = Mask(mask_keywords=["database_uri"])
    check_db()
    init_db()
    logger.info(f"Starting {PROJECT_NAME} version {VERSION}")
    logger.info(f"Settings: {mask.secrets(get_settings().model_dump())}")
    yield
    logger.info(f"Stopping application {PROJECT_NAME} version {VERSION}")
    logging.shutdown()


# todo(berry): Create factor for FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title=PROJECT_NAME,
    summary=PROJECT_DESCRIPTION,
    version=VERSION,
    openapi_url=None,
    default_response_class=HTMLResponse,
    redirect_slashes=False,
    debug=get_settings().DEBUG,
)

app.add_middleware(RequestLoggingMiddleware)
app.mount("/static", StaticFiles(directory="tad/site/static/"), name="static")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse:
    return await tad_http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> HTMLResponse:
    return await tad_validation_exception_handler(request, exc)


app.include_router(api_router)
