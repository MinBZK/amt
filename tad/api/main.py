from fastapi import APIRouter

from tad.api.routes import health, pages, root, tasks

api_router = APIRouter()
api_router.include_router(root.router)
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(pages.router, prefix="/pages", tags=["pages"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
