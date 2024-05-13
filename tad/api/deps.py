from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from tad.core.config import settings
from tad.core.db import engine

templates = Jinja2Templates(directory=settings.TEMPLATE_DIR)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
