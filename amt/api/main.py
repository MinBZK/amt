from fastapi import APIRouter

from amt.api.routes import algorithm, algorithms, auth, health, pages, root

api_router = APIRouter()
api_router.include_router(root.router)
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(pages.router, prefix="/pages", tags=["pages"])
api_router.include_router(algorithms.router, prefix="/algorithm-systems", tags=["algorithm-systems"])
api_router.include_router(algorithm.router, prefix="/algorithm-system", tags=["algorithm-system"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
