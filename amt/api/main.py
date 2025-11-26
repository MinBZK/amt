from fastapi import APIRouter

from amt.api.routes import algorithm, algorithms, auth, health, organizations, pages, publish, root

api_router: APIRouter = APIRouter()
api_router.include_router(root.router)
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(pages.router, prefix="/pages", tags=["pages"])
api_router.include_router(algorithms.router, prefix="/algorithms", tags=["algorithms"])
api_router.include_router(algorithm.router, prefix="/algorithm", tags=["algorithm"])
api_router.include_router(publish.router, prefix="/algorithm", tags=["publish"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
