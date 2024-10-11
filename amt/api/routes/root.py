import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from amt.api.deps import templates

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/")
async def base(request: Request) -> HTMLResponse:
    breadcrumbs = {}

    return templates.TemplateResponse(request, "pages/landingpage.html.j2", {"breadcrumbs": breadcrumbs})
