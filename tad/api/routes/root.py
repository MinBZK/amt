from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from tad.repositories.deps import templates

router = APIRouter()


@router.get("/")
async def base(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="root/index.html")
