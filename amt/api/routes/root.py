import logging

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/")
async def base() -> RedirectResponse:
    return RedirectResponse("/projects/")
