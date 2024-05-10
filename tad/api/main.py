from fastapi import APIRouter

from tad.api.routes import health, root

api_router = APIRouter()
api_router.include_router(root.router)
api_router.include_router(health.router, prefix="/health", tags=["health"])
