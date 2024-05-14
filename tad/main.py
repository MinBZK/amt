import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from tad.api.main import api_router
from tad.core.config import settings
from tad.core.db import check_db
from tad.core.exception_handlers import (
    http_exception_handler as tad_http_exception_handler,
)
from tad.core.exception_handlers import (
    validation_exception_handler as tad_validation_exception_handler,
)
from tad.core.log import configure_logging
from tad.middleware.route_logging import RequestLoggingMiddleware
from tad.utils.mask import Mask

from .routers import pages, tasks

configure_logging(settings.LOGGING_LEVEL, settings.LOGGING_CONFIG)


logger = logging.getLogger(__name__)
mask = Mask(mask_keywords=["database_uri"])


# todo(berry): move lifespan to own file
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} version {settings.VERSION}")
    logger.info(f"Settings: {mask.secrets(settings.model_dump())}")
    # todo(berry): setup database connection
    await check_db()
    yield
    logger.info(f"Stopping application {settings.PROJECT_NAME} version {settings.VERSION}")
    logging.shutdown()


templates = Jinja2Templates(directory="templates")

app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    summary=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=None,
    default_response_class=HTMLResponse,
    redirect_slashes=False,
)

app.add_middleware(RequestLoggingMiddleware)
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
app.include_router(tasks.router)
app.include_router(pages.router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse:
    return await tad_http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> HTMLResponse:
    return await tad_validation_exception_handler(request, exc)


app.include_router(api_router)
