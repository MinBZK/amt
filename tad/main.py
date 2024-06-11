import logging
import re
from contextlib import asynccontextmanager

import yaml
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlmodel import SQLModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from tad.api.main import api_router
from tad.core.config import settings
from tad.core.db import check_db, get_engine
from tad.core.exception_handlers import (
    http_exception_handler as tad_http_exception_handler,
)
from tad.core.exception_handlers import (
    validation_exception_handler as tad_validation_exception_handler,
)
from tad.core.log import configure_logging
from tad.utils.mask import Mask

from .middleware.route_logging import RequestLoggingMiddleware
from .models import Status, Task
from .repositories.statuses import StatusesRepository
from .repositories.tasks import TasksRepository

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
    SQLModel.metadata.drop_all(get_engine())
    SQLModel.metadata.create_all(get_engine())
    session = scoped_session(sessionmaker(bind=get_engine()))
    task_repository = TasksRepository(session)
    statuses_repository = StatusesRepository(session)
    statuses_repository.save(Status(id=1, name="todo", sort_order=1))
    statuses_repository.save(Status(id=2, name="in_progress", sort_order=2))
    statuses_repository.save(Status(id=3, name="review", sort_order=3))
    statuses_repository.save(Status(id=4, name="done", sort_order=4))
    with open("sources/iama.yaml") as f:
        questionnaire = yaml.safe_load(f)
    sort_order = 0
    for question in questionnaire["tasks"]:
        sort_order = sort_order + 1
        task: Task = Task()
        task.sort_order = sort_order
        task.description = re.split(r"[.?]", question["question"])[0]
        task.title = "IAMA " + question["urn"]
        task.status_id = 1
        task_repository.save(task)
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
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse:
    return await tad_http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> HTMLResponse:
    return await tad_validation_exception_handler(request, exc)


app.include_router(api_router)

# todo (robbert) add init code for example tasks and statuses
