from fastapi import APIRouter
from .category import router as category_router
from .brand import router as brand_router
from .product import router as product_router

router = APIRouter()
router.include_router(category_router)
router.include_router(brand_router)
router.include_router(product_router)
