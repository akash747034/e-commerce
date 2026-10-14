from fastapi import APIRouter
from .brand import router as brand_router
from .category import router as category_router
from .coupon import router as coupon_router
from .dashboard import router as dashboard_router
from .order import router as order_router
from .user import router as user_router

router = APIRouter(prefix="/admin")

# Platform Administration Modules
router.include_router(dashboard_router)
router.include_router(user_router)
router.include_router(category_router)
router.include_router(brand_router)
router.include_router(order_router)
router.include_router(coupon_router)
