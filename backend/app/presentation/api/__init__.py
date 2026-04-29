from fastapi import APIRouter

from .app_api import router as app_api_router

router = APIRouter(prefix="/api")

router.include_router(app_api_router)
