import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from amt.api.deps import templates
from amt.core.authorization import no_authorization

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/")
@no_authorization
async def base(request: Request) -> HTMLResponse:
    breadcrumbs = {}

    return templates.TemplateResponse(request, "pages/landingpage.html.j2", {"breadcrumbs": breadcrumbs})
