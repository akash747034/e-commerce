from fastapi import APIRouter
from .cart import router as cart_router
from .order import router as order_router
from .review import router as review_router
from .wishlist import router as wishlist_router

router = APIRouter()
router.include_router(cart_router)
router.include_router(order_router)
router.include_router(review_router)
router.include_router(wishlist_router)
