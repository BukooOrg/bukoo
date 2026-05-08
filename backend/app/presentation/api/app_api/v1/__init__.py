from fastapi import APIRouter

from .auth_routes import router as auth_router
from .collection_routes import router as collection_router
from .health_routes import router as health_router
from .user_routes import router as user_router

router = APIRouter(prefix="/v1")

router.include_router(auth_router)
router.include_router(collection_router)
router.include_router(health_router)
router.include_router(user_router)
