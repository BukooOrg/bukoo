from fastapi import APIRouter

from .auth_routes import router as auth_router
from .author_routes import router as author_router
from .book_routes import router as book_router
from .cart_routes import router as cart_router
from .category_routes import router as category_router
from .collection_routes import router as collection_router
from .health_routes import router as health_router
from .user_routes import router as user_router

router = APIRouter(prefix="/v1")

router.include_router(auth_router)
router.include_router(book_router)
router.include_router(cart_router)
router.include_router(category_router)
router.include_router(collection_router)
router.include_router(health_router)
router.include_router(user_router)
router.include_router(author_router)
