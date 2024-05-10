from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/live", response_class=JSONResponse)
async def liveness():
    return {"status": "ok"}


@router.get("/ready", response_class=JSONResponse)
async def readiness():
    # todo(berry): Add database connection check
    return {"status": "ok"}
