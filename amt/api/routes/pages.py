from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from amt.api.deps import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def default_layout(
    request: Request,
) -> HTMLResponse:
    return templates.TemplateResponse(request, "pages/index.html.j2", {})
