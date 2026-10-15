from fastapi import APIRouter
from .dashboard import router as dashboard_router
from .order import router as order_router
from .product import router as product_router
from .shipment import router as shipment_router

router = APIRouter(prefix="/seller")

# Seller Portal Sub-Routers
router.include_router(dashboard_router)
router.include_router(product_router)
router.include_router(order_router)
router.include_router(shipment_router)
