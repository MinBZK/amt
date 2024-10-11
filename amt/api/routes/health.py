from fastapi import APIRouter
from fastapi.responses import JSONResponse

from amt.core.authorization import no_authorization

router = APIRouter()


@router.get("/live", response_class=JSONResponse)
@no_authorization
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", response_class=JSONResponse)
@no_authorization
async def readiness() -> dict[str, str]:
    # todo(berry): Add database connection check
    return {"status": "ok"}
