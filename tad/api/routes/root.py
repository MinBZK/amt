from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse

from tad.core.config import settings
from tad.repositories.deps import templates

router = APIRouter()


@router.get("/")
async def base(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="root/index.html")


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(settings.STATIC_DIR + "/favicon.ico")
