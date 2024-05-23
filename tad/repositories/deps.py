from collections.abc import Generator

from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from tad.core.config import settings
from tad.core.db import get_engine

templates = Jinja2Templates(directory=settings.TEMPLATE_DIR)


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
