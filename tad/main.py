import logging

from fastapi import FastAPI
from sqlmodel import Session, select
from starlette.middleware.cors import CORSMiddleware

from tad.core.config import settings
from tad.core.db import engine, init_db
from tad.models import Hero

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/")
async def root():
    init_db()
    # with Session(engine) as session:
    #     statement = select(UserBase).where(UserBase.full_name == "Spider-Boy")
    #     hero = session.exec(statement).first()
    #     print(hero)

    return {"message": "Hello World"}
