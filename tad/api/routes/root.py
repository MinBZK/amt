from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

from tad.core.config import settings

router = APIRouter()


@router.get("/")
async def base() -> RedirectResponse:
    return RedirectResponse("/pages/")


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(settings.STATIC_DIR + "/favicon.ico")
