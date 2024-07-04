from fastapi import APIRouter
from fastapi.responses import JSONResponse

from tad.core.config import VERSION

router = APIRouter()


@router.get("/live", response_class=JSONResponse)
async def liveness():
    return {"status": "ok", "version": VERSION}


@router.get("/ready", response_class=JSONResponse)
async def readiness():
    # todo(berry): Add database connection check
    return {"status": "ok", "version": VERSION}
