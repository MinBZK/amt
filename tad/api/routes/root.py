from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/")
async def base():
    return HTMLResponse(content="message   - Hello World 2 sdfasdfsda")
