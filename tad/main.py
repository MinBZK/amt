import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from tad.core.config import settings
from tad.core.logger import set_default_logging_setup
from tad.middleware.routelogging import RequestLoggingMiddleware
from tad.utils.mask import DataMasker

set_default_logging_setup()
logger = logging.getLogger(__name__)
data_masker = DataMasker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} version {settings.VERSION}")
    logger.info(f"Settings: {data_masker.mask_data(settings.model_dump())}")
    # todo(berry): setup database connection
    yield
    logger.info(f"Stopping application {settings.PROJECT_NAME} version {settings.VERSION}")
    logging.shutdown()


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    summary=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url=None,
    default_response_class=HTMLResponse,
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return HTMLResponse(
        status_code=exc.status_code,
        content=f"<h1>{exc.status_code}</h1><p>{exc.detail}</p>",
    )


app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    # todo(berry): what if BACKEND_CORS_ORIGINS is not set?
    allow_origins=[str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return HTMLResponse(content="message   - Hello World 2 sdfasdfsda")
