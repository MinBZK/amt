import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from amt.api.deps import templates

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/debug-headers")
async def debug_headers(request: Request) -> PlainTextResponse:
    """Temporary endpoint to debug proxy headers. Remove after troubleshooting."""
    lines = [
        "=== Request URL Info ===",
        f"request.url: {request.url}",
        f"request.url.scheme: {request.url.scheme}",
        f"request.url.hostname: {request.url.hostname}",
        f"request.base_url: {request.base_url}",
        "",
        "=== Forwarded Headers ===",
        f"X-Forwarded-Proto: {request.headers.get('x-forwarded-proto', 'NOT SET')}",
        f"X-Forwarded-Host: {request.headers.get('x-forwarded-host', 'NOT SET')}",
        f"X-Forwarded-For: {request.headers.get('x-forwarded-for', 'NOT SET')}",
        f"X-Forwarded-Port: {request.headers.get('x-forwarded-port', 'NOT SET')}",
        f"Forwarded: {request.headers.get('forwarded', 'NOT SET')}",
        "",
        "=== All Headers ===",
    ]
    for key, value in sorted(request.headers.items()):
        lines.append(f"{key}: {value}")

    return PlainTextResponse("\n".join(lines))


@router.get("/")
async def base(request: Request) -> HTMLResponse:
    breadcrumbs = {}

    return templates.TemplateResponse(request, "pages/landingpage.html.j2", {"breadcrumbs": breadcrumbs})
